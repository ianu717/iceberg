import traceback

from contextlib import asynccontextmanager

import faiss
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
from fastapi.middleware.cors import CORSMiddleware

from .chat.config import EMBEDDING_MODEL, FAISS_TOP_K, RAG_DIR
from .chat.index_loader import load_indexes
from .chat.llm import call_llm, init_llm
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

    #  # ✅ Cargar TODOS los índices (global + territoriales)
    # app.state.indexes = load_indexes(RAG_DIR)
    # import traceback

    try:
        state.indexes = load_indexes(RAG_DIR)
    except Exception as e:
        print("ERROR AL CARGAR ÍNDICES:")
        traceback.print_exc()

    # print("⏳ Cargando índice FAISS y metadatos...")
    # state.index    = load_faiss_index()
    # state.metadata = load_metadata()

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

origins = [
    "http://localhost:5500",        # tu frontend en local
    "https://tu-frontend.onrender.com",  # tu frontend en producción
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
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
    places = retrieve(
        query=query,
        model=state.model,
        indexes=state.indexes,  # ← cambia aquí
        k = FAISS_TOP_K
    )

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
