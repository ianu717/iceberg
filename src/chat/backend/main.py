"""
Txoko — Backend FastAPI
"""

from contextlib import asynccontextmanager

import faiss
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
from fastapi.middleware.cors import CORSMiddleware
from .chat.config import EMBEDDING_MODEL
from .chat.index_loader import load_faiss_index, load_metadata
from .chat.llm import call_llm, init_llm
#from rag.llm import call_llm, init_gemini
from .chat.prompt import build_prompt
from .chat.retrieval import retrieve


# ── Estado global en memoria ───────────────────────────────────────────────

class AppState:
    index:    faiss.Index
    metadata: list[dict]
    model:    SentenceTransformer

state = AppState()


# ── Lifespan: carga única al arrancar ─────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("⏳ Cargando modelo de embeddings...")
    state.model = SentenceTransformer(EMBEDDING_MODEL)

    print("⏳ Cargando índice FAISS y metadatos...")
    state.index    = load_faiss_index()
    state.metadata = load_metadata()

    # print("⏳ Inicializando Gemini...")
    # init_gemini()
    # print("⏳ Inicializando Groq...")
    init_llm()

    print("✅ Aupa backend listo.")
    yield
    # teardown (si fuera necesario en el futuro)


# ── App ────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="Aupa — Chatbot turístico de Euskadi",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Schemas ────────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    query: str

class ChatResponse(BaseModel):
    answer: str


# ── Endpoints ──────────────────────────────────────────────────────────────

@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    query = request.query.strip()

    if not query:
        raise HTTPException(status_code=422, detail="La query no puede estar vacía.")

    # 1. Retrieve
    places = retrieve(query, state.model, state.index, state.metadata)

    # DEBUG TEMPORAL — borrar cuando termines de diagnosticar
    print(f"DEBUG lugares encontrados: {len(places)}")
    for p in places:
        print(f"  score={p.get('_score', 0):.3f} | {p.get('nombre')} — {p.get('municipio')}")

    if not places:
        return ChatResponse(answer="No he encontrado lugares relevantes para tu consulta.")

    # 2. Build prompt
    prompt, system = build_prompt(query, places)

    # 3. Call LLM
    try:
        answer = call_llm(prompt, system)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Error al llamar al LLM: {e}")

    return ChatResponse(answer=answer)
