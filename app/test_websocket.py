import asyncio
import websockets


async def main():

    uri = "ws://127.0.0.1:8000/ws/orders/1"

    async with websockets.connect(uri) as websocket:

        print("WebSocket connected successfully!")
        print("Waiting for events...")

        message = await websocket.recv()

        print("Received event:")
        print(message)


asyncio.run(main())