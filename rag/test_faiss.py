import json
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

# Cargar índice y metadatos
index = faiss.read_index("rag_assets/faiss_index.index")
with open("rag_assets/faiss_metadata.json", encoding="utf-8") as f:
    metadata = json.load(f)

# Cargar el mismo modelo que se usó para generar los embeddings
model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")

def buscar(pregunta, k=5):
    print(f"\nPregunta: '{pregunta}'")
    print("-" * 50)
    
    # Convertir la pregunta a embedding
    embedding = model.encode([pregunta], normalize_embeddings=True)
    
    # Buscar los k más similares en FAISS
    scores, indices = index.search(embedding.astype(np.float32), k)
    
    for score, idx in zip(scores[0], indices[0]):
        lugar = metadata[idx]
        print(f"  [{score:.3f}] {lugar['nombre']} — {lugar['municipio']} ({lugar['categoria']})")

# Pruebas
buscar("restaurante pintxos Bilbao")
buscar("restaurante Bilbao")
buscar("hotel rural Bizkaia")
buscar("playa Zarautz")
buscar("cerca del guggenheim")
buscar("rutas cerca de bilbao", k=20)