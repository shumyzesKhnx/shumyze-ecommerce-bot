
import os
import json

from dotenv import load_dotenv
from groq import AsyncGroq
from fastapi import FastAPI, WebSocket, WebSocketDisconnect

from ingest import search_faq


# Load environment variables
load_dotenv()


# Initialize Groq client
client = AsyncGroq(
    api_key=os.getenv("GROQ_API_KEY")
)

MODEL = os.getenv("GROQ_MODEL")


# Initialize FastAPI application
app = FastAPI()


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
                "You are ShopMate, an E-Commerce Customer Support Assistant. "
                "Help customers with orders, returns, shipping and warranties. "
                "Be polite, friendly and professional. "

                "When a customer asks about a specific order, use the "
                "get_order_status tool to retrieve its information. "
                "Never invent order information or claim an order status "
                "without checking the tool. "

                "STRICT FAQ AND POLICY RULES: "
                "Use retrieved FAQ information as the only source of "
                "confirmed company policies. "
                "Never invent or assume return conditions, refund timelines, "
                "exchange guarantees, shipping charges, warranty coverage, "
                "email addresses, phone numbers or contact links. "
                "Do not promise prepaid return labels, refunds or exchanges "
                "unless the retrieved FAQ explicitly confirms them. "
                "If the FAQ does not contain the answer, politely explain "
                "that you do not have confirmed information and recommend "
                "contacting the company's support team. "
                "You may ask for an order number when necessary, but do not "
                "claim you can verify return eligibility unless an "
                "appropriate tool provides that information. "
                "Accuracy is more important than giving a complete-sounding "
                "answer."
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
                        f"Category: {item['category']}\n"
                        f"FAQ Answer: {item['answer']}"
                        for item in faq_results
                    ]
                )

                user_content = (
                    f"Customer question: {user_message}\n\n"
                    f"Retrieved FAQ information:\n{faq_context}\n\n"
                    "Instructions:\n"
                    "- Answer using only the retrieved FAQ information "
                    "for company policies.\n"
                    "- Do not add details that are not present in the FAQs.\n"
                    "- If the FAQs do not fully answer the question, "
                    "clearly mention what information is unavailable.\n"
                    "- You may ask relevant follow-up questions, such as "
                    "the customer's order number.\n"
                )

            else:

                user_content = (
                    f"Customer question: {user_message}\n\n"
                    "No relevant FAQ information was found.\n"
                    "Do not guess or invent company policies.\n"
                    "Politely explain that you do not have confirmed "
                    "information and recommend contacting customer support."
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
                        f"\n[TOOL CALL] Function requested: {function_name}"
                    )

                    print(
                        f"[TOOL CALL] Arguments: "
                        f"{tool_call.function.arguments}"
                    )

                    arguments = json.loads(
                        tool_call.function.arguments
                    )

                    print(f"[TOOL EXECUTION] Executing {function_name}...")

                    if function_name == "get_order_status":

                        result = get_order_status(
                            arguments["order_id"]
                        )

                        print(f"[TOOL RESULT] {result}")

                    else:

                        print(
                            f"[WARNING] Unexpected tool name: {function_name}"
                        )

                        result = {"error": "Unknown function"}

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
