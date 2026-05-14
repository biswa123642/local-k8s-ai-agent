from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import httpx
import os

app = FastAPI(title="Local K8s AI Agent")

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://ollama:11434")
MODEL = os.getenv("MODEL", "mistral")

SYSTEM_PROMPT = """You are a DevOps assistant specializing in Kubernetes.
When given an error or question, you:
1. Explain what it means clearly
2. Provide the exact kubectl commands to diagnose or fix it
3. Explain why the fix works
Be concise and practical."""


class Query(BaseModel):
    question: str


class Answer(BaseModel):
    answer: str
    model: str


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/ask", response_model=Answer)
async def ask(query: Query):
    payload = {
        "model": MODEL,
        "prompt": query.question,
        "system": SYSTEM_PROMPT,
        "stream": False,
    }
    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            resp = await client.post(f"{OLLAMA_URL}/api/generate", json=payload)
            resp.raise_for_status()
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"Ollama unreachable: {e}")

    data = resp.json()
    return Answer(answer=data["response"], model=MODEL)


@app.get("/models")
async def list_models():
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(f"{OLLAMA_URL}/api/tags")
        return resp.json()
