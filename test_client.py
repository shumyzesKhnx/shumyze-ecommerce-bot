
import asyncio
import json
import websockets


async def chat():

    uri = "ws://127.0.0.1:8000/ws/chat"

    async with websockets.connect(uri) as websocket:

        # Outer loop: keep the conversation running
        while True:

            user_message = input("\nYou: ")

            if user_message.lower() == "exit":
                print("Closing chat...")
                break

            await websocket.send(user_message)

            print("ShopMate: ", end="", flush=True)

            # Inner loop: receive one complete response
            while True:

                response = await websocket.recv()
                data = json.loads(response)

                if data["type"] == "token":

                    print(data["content"], end="", flush=True)

                elif data["type"] == "done":

                    print("\n")
                    break


if __name__ == "__main__":
    asyncio.run(chat())
