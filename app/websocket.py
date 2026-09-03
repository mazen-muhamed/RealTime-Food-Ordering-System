import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from .message_bus import redis


router = APIRouter()


@router.websocket("/ws/orders/{order_id}")
async def order_websocket(
    websocket: WebSocket,
    order_id: int
):

    await websocket.accept()

    pubsub = redis.pubsub()

    channel = f"order:{order_id}"

    await pubsub.subscribe(channel)

    try:

        async for message in pubsub.listen():

            if message["type"] != "message":
                continue

            event = json.loads(message["data"])

            await websocket.send_json(event)

    except WebSocketDisconnect:

        print(
            f"Client disconnected from order {order_id}"
        )

    finally:

        await pubsub.unsubscribe(channel)
        await pubsub.close()