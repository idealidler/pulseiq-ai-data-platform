from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    question: str = Field(min_length=1)
    debug: bool = False


class ChatResponse(BaseModel):
    answer: str
    route: str
    evidence: list[dict[str, Any]]
    debug: dict[str, Any] | None = None
