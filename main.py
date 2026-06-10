import asyncio
import json
import os

import anthropic
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

FAKE_RESPONSE = (
    "Server-Sent Events allow a server to push data to a browser over a single "
    "long-lived HTTP connection. Unlike WebSockets, SSE is one-directional: the "
    "server streams messages and the client listens. This makes SSE ideal for "
    "live feeds, progress updates, and LLM token streaming — exactly what you're "
    "seeing right now. Each message arrives as plain text, prefixed with 'data:', "
    "and the browser's built-in EventSource API handles reconnection automatically."
)


@app.get("/")
async def index():
    return FileResponse("index.html")


@app.get("/stream")
async def stream(prompt: str = "", request: Request = None):
    tokens = FAKE_RESPONSE.split(" ")

    async def event_generator():
        for i, word in enumerate(tokens):
            if request and await request.is_disconnected():
                break
            payload = json.dumps({"token": word + " "})
            yield f"id: {i}\ndata: {payload}\n\n"
            await asyncio.sleep(0.05)
        yield "event: done\ndata: {}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.get("/stream-real")
async def stream_real(prompt: str = "", request: Request = None):
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        async def error_gen():
            payload = json.dumps({"token": "[Error: ANTHROPIC_API_KEY not set] "})
            yield f"data: {payload}\n\n"
            yield "event: done\ndata: {}\n\n"
        return StreamingResponse(error_gen(), media_type="text/event-stream")

    client = anthropic.Anthropic(api_key=api_key)

    async def event_generator():
        i = 0
        try:
            with client.messages.stream(
                model="claude-opus-4-8",
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt or "Say hello."}],
            ) as stream:
                for text in stream.text_stream:
                    if request and await request.is_disconnected():
                        break
                    payload = json.dumps({"token": text})
                    yield f"id: {i}\ndata: {payload}\n\n"
                    i += 1
        except Exception as e:
            payload = json.dumps({"token": f"[Error: {e}] "})
            yield f"data: {payload}\n\n"
        yield "event: done\ndata: {}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
#this is a comment to save the streak