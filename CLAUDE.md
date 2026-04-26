# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Jain QA Agent — an AI-powered Q&A system for the Jain community providing answers about Digambar Jain scriptures, Tirthankaras, and practices. Uses a ReAct agent with LangChain, Google Gemini (2.5 Flash), and FAISS vector search. Responds in Hindi.

## Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Start FastAPI backend (port 8000)
python main.py

# Start Streamlit frontend (port 8501, separate terminal)
streamlit run app.py
```

No test suite exists.

## Architecture

Two-process architecture: a FastAPI backend and a Streamlit frontend communicating over HTTP.

**`main.py`** — FastAPI backend. Core components:
- `POST /upload` — indexes documents (raw text or file upload) into a shared FAISS vector store (`faiss_index_shared/`). Requires `x-api-key` header with Gemini API key.
- `POST /chat` — runs a LangChain ReAct agent (legacy `create_react_agent`) against the vector store. Uses `ConversationBufferMemory` keyed by session ID. A custom Hindi prompt template defines agent behavior and tool usage.
- The FAISS index is loaded once at startup and updated in-place on uploads.

**`app.py`** — Streamlit frontend. Provides a chat UI and a "Knowledge Feed" admin section for uploading documents. Sends requests to the backend. Session IDs are UUID-based. Backend URL configurable via `API_URL` env var (defaults to `http://127.0.0.1:8000`).

## Deployment

- **Backend (FastAPI)**: https://jain-api.onrender.com (Swagger docs at /docs)
- **Frontend (Streamlit)**: https://jain-qa-agent.onrender.com

## Environment

Requires a Google Gemini API key. The frontend collects it via a sidebar input and passes it as `x-api-key` header. The backend also reads `GOOGLE_API_KEY` from environment for embedding initialization.
