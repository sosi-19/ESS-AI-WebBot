
from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str
    file_id: str | None = None


class ChatResponse(BaseModel):
    response: str
