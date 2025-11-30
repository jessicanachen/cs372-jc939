import json
import numpy as np
import faiss
import os
from sentence_transformers import SentenceTransformer
from openai import OpenAI
from pathlib import Path
from dotenv import load_dotenv 

ROOT_DIR = Path(__file__).resolve().parents[1]

load_dotenv(ROOT_DIR / ".env")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY is not set. Check your .env or environment.")

client = OpenAI(api_key=OPENAI_API_KEY)

"""## Setup"""

BASE_DIR = Path(__file__).resolve().parent

DATA_DIR = BASE_DIR / "data"
INDEX_PATH = DATA_DIR / "pokemon_faiss.index"
META_PATH  = DATA_DIR / "pokemon_metadata.json"

# load FAISS
index = faiss.read_index(str(INDEX_PATH))
with open(META_PATH, "r", encoding="utf-8") as f:
    corpus_meta = json.load(f)

print(f"Loaded {len(corpus_meta)} chunks from metadata.")
print(f"FAISS index has {index.ntotal} vectors.")

# embedding model used for indexing
embed_model = SentenceTransformer("all-MiniLM-L6-v2")

"""## Retrieval (pure dense RAG)"""

def dense_search(query: str, top_k: int = 50, debug: bool = False):
    q_vec = embed_model.encode([query], convert_to_tensor=False).astype("float32")
    D, I = index.search(q_vec, top_k)
    D, I = D[0], I[0]

    results = []
    for rank, (dist, idx) in enumerate(zip(D, I), start=1):
        idx = int(idx)
        score = -float(dist)  # higher = more similar
        doc = corpus_meta[idx]
        results.append(
            {
                "idx": idx,
                "score": score,
                "doc": doc,
            }
        )

        if debug:
            text = doc.get("text", "")
            pokemon = doc.get("pokemon", "Unknown")
            section = doc.get("section", "unknown-section")
            print(f"DENSE #{rank} | idx={idx} | score={score:.4f} | [{pokemon} — {section}]")
            print(text[:300].replace("\n", " "))
            if len(text) > 300:
                print("... [truncated]")
            print()

    return results

def build_context(results, max_chars: int = 4000):
    parts = []
    total_len = 0

    for r in results:
        m = r["doc"]
        header = f"[{m.get('pokemon', 'Unknown')} — {m.get('section', 'unknown-section')}]"
        desc = m.get("description") or ""
        text = m.get("text") or ""

        chunk_str = header + "\n"
        if desc:
            chunk_str += desc + "\n"
        chunk_str += text + "\n"

        if total_len + len(chunk_str) > max_chars:
            break

        parts.append(chunk_str)
        total_len += len(chunk_str)

    return "\n".join(parts)

"""## Text Generation"""

def answer_with_rag(query: str, k: int = 8, debug: bool = False) -> str:
    # pure dense retrieval
    results = dense_search(query=query, top_k=k, debug=debug)

    context = build_context(results)

    prompt = f"""You are a helpful Pokédex assistant for all generations of Pokémon.
Use ONLY the provided context when answering – if the context does not contain
the answer, say you don't know.

Context:
{context}

User question: {query}
Answer in a concise paragraph, including specific numbers, names, and conditions when relevant.
"""

    if debug:
        print("\n================== CONTEXT USED ==================\n")
        print(context)

    response = client.responses.create(
        model="gpt-5-mini",
        input=prompt,
    )

    return response.output_text
