from __future__ import annotations

import json

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from api.schemas.chat import ChatRequest, ChatResponse
from api.services.chat_service import answer_question


app = FastAPI(title="PulseIQ API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    result = answer_question(request.question, debug=request.debug)
    return ChatResponse(**result)


def _chunk_text(text: str, chunk_size: int = 220) -> list[str]:
    if not text.strip():
        return []
    chunks: list[str] = []
    current = ""

    for line in text.splitlines(keepends=True):
        if len(current) + len(line) > chunk_size and current:
            chunks.append(current)
            current = line
        else:
            current += line

    if current:
        chunks.append(current)

    return chunks


@app.post("/chat/stream")
def chat_stream(request: ChatRequest) -> StreamingResponse:
    def event_stream():
        yield f"event: status\ndata: {json.dumps({'message': 'Opening the pipeline...'}, default=str)}\n\n"
        yield f"event: status\ndata: {json.dumps({'message': 'Routing between SQL and semantic retrieval...'}, default=str)}\n\n"
        yield f"event: status\ndata: {json.dumps({'message': 'Gathering evidence from the data stack...'}, default=str)}\n\n"

        try:
            result = answer_question(request.question, debug=request.debug)
        except Exception as exc:
            yield f"event: error\ndata: {json.dumps({'message': str(exc)}, default=str)}\n\n"
            return

        yield f"event: status\ndata: {json.dumps({'message': 'Synthesizing the final answer...'}, default=str)}\n\n"
        for chunk in _chunk_text(result["answer"]):
            yield f"event: answer_delta\ndata: {json.dumps({'delta': chunk}, default=str)}\n\n"

        payload = {
            "route": result["route"],
            "evidence": result["evidence"],
            "debug": result.get("debug"),
        }
        yield f"event: complete\ndata: {json.dumps(payload, default=str)}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
