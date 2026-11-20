
from fastapi.responses import FileResponse
from pathlib import Path
import os
import json

from dotenv import load_dotenv
from groq import AsyncGroq
from fastapi import FastAPI, WebSocket, WebSocketDisconnect

from ingest import search_faq


# Project paths
BASE_DIR = Path(__file__).resolve().parent

# Load environment variables
load_dotenv(BASE_DIR / ".env")


# Initialize Groq client
client = AsyncGroq(
    api_key=os.getenv("GROQ_API_KEY")
)

MODEL = os.getenv("GROQ_MODEL")


# Initialize FastAPI application
app = FastAPI()


# Serve the frontend
@app.get("/")
async def home():
    return FileResponse(BASE_DIR / "index.html")


# Mock order database
orders = {
    "1025": {
        "customer": "Ali",
        "status": "Shipped",
        "delivery": "20 November"
    },

    "1026": {
        "customer": "Ahmed",
        "status": "Processing",
        "delivery": "22 November"
    },

    "1027": {
        "customer": "Sara",
        "status": "Delivered",
        "delivery": "16 November"
    }
}


# Function to retrieve order information
def get_order_status(order_id):

    order = orders.get(order_id)

    if order:
        return order

    return {"error": "Order not found"}


# Tool schema for Groq
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_order_status",
            "description": (
                "Retrieve the status and delivery information "
                "of a customer's order using the order ID."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {
                        "type": "string",
                        "description": "The unique ID of the customer's order."
                    }
                },
                "required": ["order_id"]
            }
        }
    }
]


# Create WebSocket endpoint
@app.websocket("/ws/chat")
async def chat(websocket: WebSocket):

    await websocket.accept()

    # Conversation history for this WebSocket session
    messages = [
        {
            "role": "system",
            "content": (
                "You are ShopMate, an E-Commerce Customer Support "
                "Assistant. Help customers with orders, returns, "
                "shipping and warranties. Be friendly, natural, "
                "polite and concise.\n\n"

                "ORDER INFORMATION: "
                "When a customer asks about a specific order, use "
                "the get_order_status tool. Never invent order "
                "information or claim an order status without "
                "checking the tool.\n\n"

                "FAQ EVIDENCE RULES: "
                "Retrieved FAQ answers are the only source of "
                "confirmed company policies available to you. "
                "Treat FAQ answers as exact evidence, not as "
                "permission to make assumptions or draw additional "
                "conclusions. Do not infer eligibility, approvals, "
                "guarantees, refunds, replacements, return labels, "
                "shipping costs, deadlines, procedures or outcomes "
                "unless the retrieved information explicitly "
                "confirms them. A possibility is not a confirmed "
                "company policy. If an FAQ does not explicitly "
                "answer a question, say that you cannot confirm "
                "the information.\n\n"

                "CONTACT INFORMATION: "
                "Never invent or assume company email addresses, "
                "phone numbers, websites, links, contact forms, "
                "support channels or contact procedures. Mention "
                "a contact method only if it is explicitly "
                "provided in verified information. The phrase "
                "'contact customer support' in an FAQ does not "
                "authorize you to invent how the customer can "
                "contact them. If no verified contact method "
                "is available, say so honestly.\n\n"

                "IMAGE LIMITATION: "
                "This chat interface does not support image "
                "uploads. Never ask customers to upload or "
                "attach photographs here. If an FAQ mentions "
                "photographs or images, explain that this "
                "interface cannot receive them. Do not suggest "
                "email attachments, support portals, websites, "
                "phone numbers or other submission methods "
                "unless that method is explicitly confirmed "
                "in verified information.\n\n"

                "CONVERSATION: "
                "Use the conversation history to understand "
                "follow-up questions and remember information "
                "customers share during the current session, "
                "including their names. Distinguish customer-"
                "provided information from order database "
                "information. Answer the actual question "
                "directly. Do not repeatedly bring up unrelated "
                "order information. When you make a mistake, "
                "acknowledge the specific mistake and correct "
                "it. Avoid repetitive apologies."
            )
        }
    ]

    try:

        # Keep the conversation running
        while True:

            # Receive user message
            user_message = await websocket.receive_text()

            # Search relevant FAQs
            faq_results = search_faq(user_message)

            if faq_results:

                faq_context = "\n\n".join(
                    [
                        f"Question: {item.get('question', '')}\n"
                        f"Category: {item['category']}\n"
                        f"FAQ Answer: {item['answer']}"
                        for item in faq_results
                    ]
                )

                user_content = (
                    f"Customer question: {user_message}\n\n"
                    f"Retrieved FAQ information:\n{faq_context}\n\n"
                    "Use the retrieved information only when it "
                    "directly supports the answer. Do not infer "
                    "additional policies, eligibility, benefits, "
                    "procedures, guarantees or contact methods. "
                    "If the information does not answer the "
                    "question, clearly state what you cannot "
                    "confirm."
                )

            else:

                user_content = (
                    f"Customer question: {user_message}\n\n"
                    "No relevant FAQ information was found. "
                    "Do not invent policies, contact details, "
                    "procedures or services. If the question "
                    "requires company-specific information, "
                    "explain that you cannot confirm it."
                )

            # Add user message to conversation history
            messages.append({
                "role": "user",
                "content": user_content
            })

            # Tool-calling loop
            tool_rounds = 0

            while True:

                # Send conversation and available tools to Groq
                response = await client.chat.completions.create(
                    model=MODEL,
                    messages=messages,
                    tools=tools,
                    tool_choice="auto"
                )

                response_message = response.choices[0].message

                # Check whether Groq requested a tool
                if not response_message.tool_calls:
                    break

                # Save assistant's tool-call request
                messages.append(
                    response_message.model_dump(exclude_none=True)
                )

                # Execute requested functions
                for tool_call in response_message.tool_calls:

                    function_name = tool_call.function.name

                    print(
                        f"\n[TOOL CALL] Function requested: "
                        f"{function_name}"
                    )

                    print(
                        f"[TOOL CALL] Arguments: "
                        f"{tool_call.function.arguments}"
                    )

                    try:

                        arguments = json.loads(
                            tool_call.function.arguments
                        )

                        if not isinstance(arguments, dict):
                            raise ValueError(
                                "Tool arguments must be a JSON object."
                            )

                        if function_name == "get_order_status":

                            order_id = arguments.get("order_id")

                            if not isinstance(order_id, str) or not order_id.strip():

                                result = {
                                    "error": "Invalid order ID."
                                }

                            else:

                                print(
                                    f"[TOOL EXECUTION] Executing "
                                    f"{function_name}..."
                                )

                                result = get_order_status(
                                    order_id.strip()
                                )

                                print(
                                    f"[TOOL RESULT] {result}"
                                )

                        else:

                            print(
                                f"[WARNING] Unexpected tool name: "
                                f"{function_name}"
                            )

                            result = {
                                "error": "Unknown function."
                            }

                    except (json.JSONDecodeError, ValueError, TypeError) as error:

                        print(
                            f"[TOOL ERROR] {error}"
                        )

                        result = {
                            "error": "Invalid tool arguments."
                        }

                    # Send function result back to Groq
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": json.dumps(result)
                    })

                tool_rounds += 1

                if tool_rounds >= 5:

                    raise RuntimeError(
                        "Maximum tool-calling rounds exceeded."
                    )

            # Stream the final response from Groq
            stream = await client.chat.completions.create(
                model=MODEL,
                messages=messages,
                stream=True
            )

            assistant_response = ""

            async for chunk in stream:

                token = chunk.choices[0].delta.content

                if token:

                    assistant_response += token

                    await websocket.send_json({
                        "type": "token",
                        "content": token
                    })

            # Save assistant response in conversation history
            messages.append({
                "role": "assistant",
                "content": assistant_response
            })

            # Notify client that response is complete
            await websocket.send_json({
                "type": "done"
            })

    except WebSocketDisconnect:

        print("Client disconnected.")
