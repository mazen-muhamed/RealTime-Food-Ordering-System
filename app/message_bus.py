import json

from redis.asyncio import Redis


REDIS_URL = "redis://localhost:6379"

STREAM_NAME = "order_events"


redis = Redis.from_url(
    REDIS_URL,
    decode_responses=True
)


async def publish_event(event: dict):

    await redis.xadd(
        STREAM_NAME,
        {
            "data": json.dumps(event)
        }
    )


async def consume_events(last_id="0-0"):

    while True:

        events = await redis.xread(
            {
                STREAM_NAME: last_id
            },
            block=5000,
            count=10
        )

        if not events:
            continue

        for stream, messages in events:

            for message_id, data in messages:

                event = json.loads(data["data"])

                yield message_id, event

                last_id = message_id

async def publish_order_update(order_id: int, event: dict):

    channel = f"order:{order_id}"

    await redis.publish(
        channel,
        json.dumps(event)
    )