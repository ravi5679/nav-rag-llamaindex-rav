"""Request and response shapes for the API. The frontend depends on these exact fields."""
from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=2000)
    top_k: int | None = Field(default=None, ge=1, le=20)


class SourceNode(BaseModel):
    file_name: str | None
    score: float | None
    text: str


class QueryResponse(BaseModel):
    answer: str
    sources: list[SourceNode]


class IngestResponse(BaseModel):
    message: str
    documents_added: int


# ---------- auth ----------
class Credentials(BaseModel):
    email: str = Field(..., max_length=254)
    password: str = Field(..., min_length=1, max_length=128)


class AuthUser(BaseModel):
    email: str


class AuthResponse(BaseModel):
    token: str          # send as "Authorization: Bearer <token>"
    session_id: str     # send as "X-Session-Id"
    user: AuthUser
