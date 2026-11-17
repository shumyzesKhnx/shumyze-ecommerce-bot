
import asyncio
import json
import websockets


async def chat():

    uri = "ws://127.0.0.1:8000/ws/chat"

    async with websockets.connect(uri) as websocket:

        while True:
            user_message = input("\nYou: ")

            if user_message.lower() == "exit":
                break

            await websocket.send(user_message)

            print("Bot: ", end="", flush=True)

            while True:
                response = await websocket.recv()
                data = json.loads(response)

                if data["type"] == "token":
                    print(data["content"], end="", flush=True)

                elif data["type"] == "done":
                    print()
                    break


asyncio.run(chat())
