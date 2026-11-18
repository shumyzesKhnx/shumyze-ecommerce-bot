
import os
import json

from dotenv import load_dotenv
from groq import AsyncGroq
from fastapi import FastAPI, WebSocket, WebSocketDisconnect


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
                "You are an E-Commerce Customer Support Assistant. "
                "Help customers with orders, returns, shipping and warranties. "
                "Be polite and professional. "
                "When a customer asks about a specific order, "
                "use the get_order_status tool to retrieve its information. "
                "Never invent order information or claim an order status "
                "without checking the tool."
            )
        }
    ]

    try:

        # Keep the conversation running
        while True:

            # Receive user message
            user_message = await websocket.receive_text()

            messages.append({
                "role": "user",
                "content": user_message
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

                    arguments = json.loads(
                        tool_call.function.arguments
                    )

                    print(f"Tool called: {function_name}")
                    print(f"Arguments: {arguments}")

                    if function_name == "get_order_status":

                        result = get_order_status(
                            arguments["order_id"]
                        )

                    else:
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
                tools=tools,
                stream=True,
                tool_choice="none"
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
