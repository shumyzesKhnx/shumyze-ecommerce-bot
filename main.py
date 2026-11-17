
import os
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

# creating the websocket endpoint

@app.websocket("/ws/chat")
async def chat(websocket: WebSocket):

    await websocket.accept()

    messages = [
        {
            "role": "system",
            "content": (
                "You are an E-Commerce Customer Support Assistant. "
                "Help customers with orders, returns, shipping and warranties. "
                "Be polite and professional."
            )
        }
    ]

    try:
        while True:
            user_message = await websocket.receive_text()

            messages.append({
                "role": "user",
                "content": user_message
            })
            
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

            messages.append({
                "role": "assistant",
                "content": assistant_response
            })

            await websocket.send_json({
                "type": "done"
            })


    except WebSocketDisconnect:
        print("Client disconnected.")

