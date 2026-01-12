from pydantic import BaseModel


class ChatStreamResponse(BaseModel):
    delta: str = ""
    done: bool = False
    error: str = ""
