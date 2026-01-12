from psycopg import AsyncConnection
from psycopg.types.json import Jsonb
from pydantic_ai import ModelMessage, ModelMessagesTypeAdapter
from pydantic_core import to_jsonable_python


async def insert_message(conn: AsyncConnection, messages: list[ModelMessage]):
    async with conn.cursor() as cursor:
        await cursor.execute(
            "INSERT INTO messages (message) VALUES(%s)",
            (Jsonb(to_jsonable_python(messages)),),
        )


async def get_history(conn: AsyncConnection) -> list[ModelMessage]:
    async with conn.cursor() as cursor:
        await cursor.execute("SELECT message FROM messages ORDER BY id")
        rows = await cursor.fetchall()

    payloads = [row[0] for row in rows]

    batches: list[list[ModelMessage]] = [
        ModelMessagesTypeAdapter.validate_python(p) for p in payloads
    ]

    return [m for batch in batches for m in batch]
