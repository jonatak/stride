from psycopg import AsyncConnection
from psycopg.types.json import Jsonb
from pydantic_ai import ModelMessage, ModelMessagesTypeAdapter
from pydantic_core import to_jsonable_python


async def insert_message(conn: AsyncConnection, messages: list[ModelMessage]) -> int:
    async with conn.cursor() as cursor:
        await cursor.execute(
            "INSERT INTO messages (message) VALUES(%s) RETURNING id",
            (Jsonb(to_jsonable_python(messages)),),
        )
        res = await cursor.fetchone()
        assert res
        (message_id,) = res
        return message_id


async def get_history(conn: AsyncConnection) -> list[ModelMessage]:
    async with conn.cursor() as cursor:
        await cursor.execute(
            "SELECT summary, up_to_message_id FROM conversation_summaries ORDER BY id DESC LIMIT 1"
        )

        row = await cursor.fetchone()
        summary, last_id = [], 0
        if row:
            (summary, last_id) = row

        await cursor.execute(
            "SELECT message FROM messages WHERE id >= %s ORDER BY id", (last_id,)
        )
        rows = await cursor.fetchall()

        payloads = [summary] + [row[0] for row in rows]

        batches: list[list[ModelMessage]] = [
            ModelMessagesTypeAdapter.validate_python(p) for p in payloads
        ]

    return [m for batch in batches for m in batch]


async def save_summary(
    conn: AsyncConnection, messages: list[ModelMessage], last_id: int
):
    async with conn.cursor() as cursor:
        await cursor.execute(
            "INSERT INTO conversation_summaries (up_to_message_id, summary) VALUES(%s, %s)",
            (
                last_id,
                Jsonb(to_jsonable_python(messages)),
            ),
        )
