# SSE Token Streamer

A minimal full-stack demo of **Server-Sent Events (SSE)** that streams text token-by-token from a FastAPI backend to a plain-JS frontend, producing a live "typing" effect.

---

## What Are Server-Sent Events?

Server-Sent Events (SSE) is a browser standard that lets a server push data to a client over a single, long-lived HTTP connection. Unlike WebSockets, SSE is **one-directional** — the server sends, the client listens.

Each message follows a simple plain-text format:

```
id: 42
data: {"token": "Hello "}

```

The browser's built-in `EventSource` API handles the connection, automatic reconnection, and event dispatching. Named events (like `event: done`) let the server signal meaningful lifecycle moments.

**Why SSE instead of WebSockets for LLM streaming?**
- HTTP/1.1 compatible — no upgrade handshake needed
- Automatic reconnection built into the browser
- One-directional is all you need to stream tokens
- Works transparently through standard HTTP proxies

---

## How Token Streaming Works

```
Browser                        FastAPI
  │                               │
  │  GET /stream?prompt=...       │
  ├──────────────────────────────>│
  │                               │  split text into word-tokens
  │  data: {"token": "Server- "}  │  yield each token + sleep 50ms
  │<──────────────────────────────┤
  │  data: {"token": "Sent "}     │
  │<──────────────────────────────┤
  │       … more tokens …         │
  │  event: done                  │
  │<──────────────────────────────┤
  │  (EventSource closed)         │
```

1. The client opens an `EventSource` pointed at `/stream?prompt=<text>`.
2. FastAPI returns a `StreamingResponse` with `media_type="text/event-stream"`.
3. The generator yields each JSON-encoded token, waits 50 ms, and checks for client disconnect.
4. A named `done` event signals completion; the client closes the connection.

The `/stream-real` endpoint does the same thing but uses the **Anthropic SDK** (`claude-opus-4-8`) to stream actual model tokens.

---

## Project Structure

```
SSE-Token-Streamer/
├── main.py           # FastAPI backend — /stream and /stream-real
├── index.html        # Frontend — EventSource + live rendering
├── requirements.txt  # Python dependencies
└── README.md
```

---

## Running Locally

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Start the server

```bash
uvicorn main:app --reload
```

Open [http://localhost:8000](http://localhost:8000) in your browser.

### 3. (Optional) Use the real Anthropic endpoint

Set your API key, then select **Real (Anthropic)** in the UI:

```bash
export ANTHROPIC_API_KEY=sk-ant-...
uvicorn main:app --reload
```

The fake `/stream` endpoint works without any API key and is the default.

---

## API Reference

| Endpoint | Description |
|---|---|
| `GET /stream?prompt=<text>` | Fake streaming — hardcoded paragraph, 50 ms/token |
| `GET /stream-real?prompt=<text>` | Real streaming — Anthropic `claude-opus-4-8` |

Both endpoints return `text/event-stream`. Each message:

```
id: <n>
data: {"token": "<word> "}

```

Stream end:

```
event: done
data: {}

```
