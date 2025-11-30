import json
import faiss
import os
import logging
from sentence_transformers import SentenceTransformer
from openai import OpenAI
from pathlib import Path
from dotenv import load_dotenv

from .history_utils import trim_history, format_history

logger = logging.getLogger(__name__)

# env setup for api key
ROOT_DIR = Path(__file__).resolve().parents[1]

load_dotenv(ROOT_DIR / ".env")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY is not set. Check your .env or environment.")

client = OpenAI(api_key=OPENAI_API_KEY)

# resolve paths for data files
BASE_DIR = Path(__file__).resolve().parent

DATA_DIR = BASE_DIR / "data"
INDEX_PATH = DATA_DIR / "pokemon_faiss.index"
META_PATH = DATA_DIR / "pokemon_metadata.json"

# load FAISS
logger.info("Loading FAISS index from %s", INDEX_PATH)
index = faiss.read_index(str(INDEX_PATH))
with open(META_PATH, "r", encoding="utf-8") as f:
    corpus_meta = json.load(f)

logger.info(
    "Loaded %d chunks from metadata; FAISS index has %d vectors.",
    len(corpus_meta),
    index.ntotal,
)

# embedding model used for indexing
embed_model = SentenceTransformer("all-MiniLM-L6-v2")
logger.info("Loaded sentence-transformer model all-MiniLM-L6-v2")


def rewrite_query_with_history(query, history):
    '''
    First chatbot, rewrites query with context to be input into RAG.
    '''
    if history is None:
        history = []

    history = trim_history(history)
    convo = format_history(history)

    prompt = f"""You are a helpful assistant.

Your task:
Given the conversation so far and the user's latest question, 
rewrite ONLY the latest question so that it becomes a fully 
self-contained, standalone question that includes any necessary 
context from the conversation.

Rules:
- Do NOT answer the question.
- Do NOT add new information.
- Do NOT change the question if no extra informatin is needed.
- Simply restate the user's latest question so that it can be 
  understood on its own.
- It is already understood to be about Pokemon.
- Return ONLY the rewritten question, nothing else.

Conversation so far:
{convo or "(no previous conversation)"}

Latest user question:
{query}
"""

    try:
        logger.debug("Rewriting query with history")
        response = client.responses.create(
            model="gpt-5-mini",
            input=prompt,
        )
        rewritten = response.output_text.strip()
        logger.info("Rewrote query for retrieval: %s", rewritten)
        return rewritten
    except Exception:
        logger.exception("Error while rewriting query; falling back to original query")
        return query


def dense_search(query, top_k: int = 50, debug: bool = False):
    '''
    Return top k document matches with RAG retrieval.
    '''
    logger.info("Running dense_search for query='%s' top_k=%d", query, top_k)

    try:
        q_vec = embed_model.encode([query], convert_to_tensor=False).astype("float32")
        D, I = index.search(q_vec, top_k)
    except Exception:
        logger.exception("Error during dense_search (embedding or FAISS search)")
        raise

    D, I = D[0], I[0]

    results = []
    for rank, (dist, idx) in enumerate(zip(D, I), start=1):
        idx = int(idx)
        score = -float(dist)
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
            logger.debug(
                "DENSE #%d | idx=%d | score=%.4f | [%s — %s] %s%s",
                rank,
                idx,
                score,
                pokemon,
                section,
                text[:300].replace("\n", " "),
                "... [truncated]" if len(text) > 300 else "",
            )

    return results

def build_context(results, max_chars: int = 4000):
    '''
    Build context to be input into chat prompt from retrieved RAG documents.
    '''
    parts = []
    total_len = 0

    for r in results:
        m = r["doc"]
        if m.get("pokemon"):
            header = f"[{m.get('pokemon')} — {m.get('section')}]"
        else:
            header = f"[{m.get('section')}]"
        text = m.get("text") or ""

        chunk_str = header + "\n"
        chunk_str += text + "\n"

        if total_len + len(chunk_str) > max_chars:
            break

        parts.append(chunk_str)
        total_len += len(chunk_str)

    logger.debug("Built context of length %d characters", total_len)
    return "\n".join(parts)


def answer_with_rag(query, history=None, k: int = 8, debug: bool = False) -> str:
    if history is None:
        history = []

    logger.info("answer_with_rag called with query='%s'", query)

    history = trim_history(history)
    convo = format_history(history)

    rag_query = rewrite_query_with_history(query=query, history=history)

    try:
        results = dense_search(query=rag_query, top_k=k, debug=debug)
        context = build_context(results)
    except Exception:
        logger.exception("Retrieval failed for query='%s'", rag_query)
        return (
            "Sorry, I ran into a problem looking up the Pokémon data. "
            "Please try again in a moment."
        )

    if debug:
        logger.debug("RAG Context:\n%s", context)
        logger.debug("Conversation history:\n%s", convo)

    prompt = f"""You are a helpful Pokédex assistant for all generations of Pokémon.
Use ONLY the provided context when answering – if the context does not contain
the answer, say you don't know.

Conversation so far:
{convo or "(no previous conversation)"}

Context:
{context}

Current user question: {query}
Answer in a concise paragraph, including specific numbers, names, and conditions when relevant.
"""

    print("\n================== CONTEXT USED ==================\n")
    print(context)

    print("\n================== HISTORY ==================\n")
    print(convo)

    try:
        logger.info("Calling OpenAI model for generation")
        response = client.responses.create(
            model="gpt-5-mini",
            input=prompt,
        )
        reply = response.output_text
        logger.info("Successfully generated model reply")
        return reply
    except Exception:
        logger.exception("OpenAI generation failed")
        return (
            "Sorry, I had an internal error while generating this answer. "
            "Please try again shortly."
        )