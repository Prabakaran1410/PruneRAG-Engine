import os
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, File, UploadFile
from pydantic import BaseModel, Field
from .ingestion import extract_pdf, Chunk
from .metrics import calculate_rag_metrics, estimate_tokens
from .pruner import prune_context
from .retriever import HybridRetriever

retriever = HybridRetriever()


class QueryRequest(BaseModel):
    query: str = Field(min_length=2)
    enable_pruning: bool = True
    max_context_tokens: int = Field(default=2000, ge=100, le=8000)


class QueryResponse(BaseModel):
    answer: str
    sources: list[dict]
    metrics: dict


def _answer(query: str, context: list[str]) -> str:
    if not context:
        return "I could not find supporting passages. Upload a PDF and try again."
    if os.getenv("GEMINI_API_KEY"):
        try:
            from google import genai
            client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
            prompt = f"Answer using only the context.\nContext:\n{'\n'.join(context)}\nQuestion: {query}"
            return client.models.generate_content(model="gemini-1.5-flash", contents=prompt).text
        except Exception:
            pass
    return f"Local mode found {len(context)} relevant passage(s).\n\n" + "\n\n".join(context[:3])


@asynccontextmanager
async def lifespan(_: FastAPI):
    retriever.add([Chunk("PruneRAG is ready. Upload a PDF to index document context.", "system", 0)])
    yield


app = FastAPI(title="PruneRAG Engine", version="0.1.0", lifespan=lifespan)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "chunks": len(retriever.chunks)}


@app.post("/api/v1/ingest")
async def ingest(file: UploadFile = File(...)) -> dict:
    chunks = extract_pdf(await file.read(), file.filename or "upload.pdf")
    retriever.add(chunks)
    return {"filename": file.filename, "chunks_indexed": len(chunks)}


@app.post("/api/v1/query", response_model=QueryResponse)
def query(request: QueryRequest) -> QueryResponse:
    started = time.time()
    hits = [hit for hit in retriever.search(request.query) if hit["score"] >= 0.65]
    raw_context = [hit["text"] for hit in hits]
    context = prune_context(raw_context, max_tokens=request.max_context_tokens) if request.enable_pruning else raw_context
    answer = _answer(request.query, context)
    prompt = f"Question: {request.query}\nContext:\n{'\n'.join(context)}"
    metrics = calculate_rag_metrics(prompt, answer, estimate_tokens("\n".join(raw_context)), started)
    return QueryResponse(answer=answer, sources=hits[:len(context)], metrics=metrics)