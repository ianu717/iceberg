import os
from pathlib import Path
from dotenv import load_dotenv


# ── Paths ──────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent.parent  # /rag/
CHAT_DIR  = BASE_DIR / "rag_assets"

FAISS_INDEX_PATH    = CHAT_DIR / "faiss_index.index"
FAISS_METADATA_PATH = CHAT_DIR / "faiss_metadata.json"

# ── Embedding model ────────────────────────────────────────────────────────
EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

# ── Retrieval ──────────────────────────────────────────────────────────────
FAISS_TOP_K  = 50   # candidates retrieved from FAISS
FINAL_TOP_K  = 10    # places actually sent to the LLM

# ── LLM ───────────────────────────────────────────────────────────────────
load_dotenv()
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
#GEMINI_MODEL = "models/gemini-2.0-flash"
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
GROQ_MODEL   = "llama-3.1-8b-instant"

# ── System prompt ──────────────────────────────────────────────────────────
SYSTEM_PROMPT = (
    "CRITICAL INSTRUCTION: Always respond in the same language the user writes in. "
    "If the user writes in English, respond in English. "
    "If the user writes in Spanish, respond in Spanish. "
    "If the user writes in Basque (Euskera), respond in Basque. "
    "Never respond in a different language than the one the user used.\n\n"
    "Eres un asistente de recomendaciones turísticas de Euskadi llamado Aupa.\n"
    "Usa únicamente la información proporcionada en el contexto.\n"
    "No inventes datos como horarios, precios ni distancias.\n"
    "Si no tienes suficiente información, dilo claramente.\n"
    "Si los lugares no encajan bien con la pregunta, dilo explícitamente.\n"
    "Si la pregunta es geográfica como 'cerca de X', advierte que no puedes "
    "garantizar proximidad exacta y sugiere verificar en el mapa.\n"
    "Presenta máximo 3 recomendaciones, no todas las disponibles.\n"
    "Sé breve y directo, máximo 3-4 frases por recomendación.\n"
    "Si el usuario pide algo auténtico, local o alejado del turismo masivo, "
    "prioriza los lugares con mayor puntuación de autenticidad local. "
    #"Una puntuación de 60/100 o más indica un lugar genuinamente local. "
    #"Menciona esta característica cuando sea relevante para la consulta.\n"
    "Sé claro, útil y ligeramente cercano en tono.\n"
    "Si te preguntan en mal tono, repregunta educadamente \n"
)
