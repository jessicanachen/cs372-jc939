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

def extract_search_query(text: str) -> str:
    """
    Fallback: extract a search query from free-form reasoning text.

    Strategy:
    - If there's a line starting with 'QUERY:', use that.
    - Otherwise, take the last non-trivial sentence.
    """
    # Try QUERY: pattern first
    lines = text.splitlines()
    for line in reversed(lines):
        if line.strip().upper().startswith("QUERY:"):
            return line.split(":", 1)[1].strip() or text.strip()

    # Fallback: last non-trivial sentence
    sentences = text.split(".")
    for s in reversed(sentences):
        s = s.strip()
        if len(s) > 10:
            return s
    return text.strip()


def recursive_dense_retrieval(
    original_question: str,
    initial_query: str,
    max_loops: int = 4,
    k_per_step: int = 8,
    debug: bool = False,
):
    """
    Recursive retrieval (RCR-style) on top of FAISS dense_search.

    Implements:
    - Iterative refinement: each loop can adjust the search query.
    - Controlled recursion: MAX_LOOPS stops infinite loops.
    - Reasoning transparency: we keep a trace of each loop.

    Returns:
        (aggregated_results, reasoning_trace)
        - aggregated_results: list of result dicts like dense_search()
        - reasoning_trace: list of per-loop dicts for debugging / logging
    """
    logger.info(
        "Starting recursive_dense_retrieval for question='%s' initial_query='%s'",
        original_question,
        initial_query,
    )

    aggregated_results = []
    seen_idxs = set()
    reasoning_trace = []

    current_query = initial_query

    for loop in range(1, max_loops + 1):
        loop_info = {"loop": loop, "query": current_query}
        logger.debug("RCR loop %d with query='%s'", loop, current_query)

        # 1) Retrieve docs for the current query
        step_results = dense_search(
            query=current_query,
            top_k=k_per_step,
            debug=debug,
        )

        new_step_results = []
        for r in step_results:
            idx = r["idx"]
            if idx not in seen_idxs:
                seen_idxs.add(idx)
                aggregated_results.append(r)
                new_step_results.append(r)

        loop_info["num_new_docs"] = len(new_step_results)
        logger.debug(
            "RCR loop %d retrieved %d new docs (total unique=%d)",
            loop,
            len(new_step_results),
            len(aggregated_results),
        )

        # 2) Build a *shortened* context just for sufficiency / refinement reasoning
        partial_context = build_context(aggregated_results, max_chars=2000)

        # 3) Sufficiency check: do we have enough info to answer now?
        suff_prompt = f"""You are helping evaluate whether we have enough information
from a Pokédex knowledge base to answer a question.

Original question:
{original_question}

Context snippets (from the knowledge base):
{partial_context or "(no context yet)"}

Answer ONLY 'YES' or 'NO':
Do we have sufficient information in the context above to answer the original question
in a factual and specific way?
"""

        try:
            suff_resp = client.responses.create(
                model="gpt-5-mini",
                input=suff_prompt,
            )
            suff_text = (suff_resp.output_text or "").strip()
        except Exception:
            logger.exception("RCR: sufficiency check failed on loop %d", loop)
            loop_info["sufficiency_error"] = True
            reasoning_trace.append(loop_info)
            break

        loop_info["sufficiency_raw"] = suff_text
        logger.debug("RCR loop %d sufficiency response: %s", loop, suff_text)

        upper = suff_text.upper()
        if upper.startswith("YES"):
            loop_info["sufficient"] = True
            reasoning_trace.append(loop_info)
            logger.info(
                "RCR: stopping at loop %d – model judged context sufficient", loop
            )
            break

        loop_info["sufficient"] = False

        # 4) If not sufficient, ask the model what *extra* info is missing and
        #    turn that into a refined search query.
                # 4) If not sufficient, ask the model to partially ANSWER parts of the
        #    question that are already resolvable from context, and rewrite the
        #    question with those concrete values.
        refine_prompt = f"""You are refining a Pokémon-related question for retrieval
over a knowledge base.

Original user question:
{original_question}

Context snippets we already retrieved:
{partial_context or "(no context yet)"}

Your job:
- Rewrite any part of the question that can be answered from the context above.
- For each such part, rewrite the question, replacing that vague phrase with
  the concrete value from the context. 
- Do NOT guess or invent facts. Only replace parts that are clearly and directly
  supported by the context. If you are not sure, leave that part unchanged.
- Keep the meaning and intent of the question the same, but make it more explicit
  and retrieval-friendly (keep important words like PP, base power, accuracy, etc.).
- IMPORTANT: This rewrite is ONLY for retrieval, not for the final answer.
  It is acceptable to choose the most likely interpretation based on the context
  even if there is some ambiguity. Prefer a single, reasonable guess instead of
  saying "I don't know".

Output format:
1) First line: a short sentence describing what you replaced (or say
   "No changes; not enough information to rewrite the question." if nothing can be resolved).
2) Second line: start with 'QUERY: ' and then output the rewritten question
   (or the original question unchanged if nothing can be replaced).
"""

        try:
            refine_resp = client.responses.create(
                model="gpt-5-mini",
                input=refine_prompt,
            )
            refine_text = (refine_resp.output_text or "").strip()
        except Exception:
            logger.exception("RCR: refinement step failed on loop %d", loop)
            loop_info["refinement_error"] = True
            reasoning_trace.append(loop_info)
            break

        loop_info["refinement_raw"] = refine_text
        new_query = extract_search_query(refine_text)
        loop_info["refined_query"] = new_query
        logger.debug(
            "RCR loop %d refinement -> new query='%s'", loop, new_query
        )

        # Avoid getting stuck if the model fails to refine
        if not new_query or new_query == current_query:
            logger.info(
                "RCR: refinement did not change the query on loop %d; stopping.", loop
            )
            reasoning_trace.append(loop_info)
            break

        current_query = new_query
        reasoning_trace.append(loop_info)

    logger.info(
        "RCR complete: %d loops, %d unique docs retrieved",
        len(reasoning_trace),
        len(aggregated_results),
    )

    # Full trace logged for transparency / debugging
    try:
        logger.debug(
            "RCR reasoning trace:\n%s",
            json.dumps(reasoning_trace, ensure_ascii=False, indent=2),
        )
    except Exception:
        # Don't let logging errors break the app
        logger.debug("Failed to JSON-serialize RCR reasoning trace")

    return aggregated_results, reasoning_trace



def answer_with_rag(query, history=None, k: int = 8, debug: bool = False):
    if history is None:
        history = []

    logger.info("answer_with_rag called with query='%s'", query)

    history = trim_history(history)
    convo = format_history(history)

    # First, rewrite with history so retrieval sees a fully self-contained question
    rag_query = rewrite_query_with_history(query=query, history=history)

    try:
        # --- NEW: recursive retrieval ---
        results, rcr_trace = recursive_dense_retrieval(
            original_question=query,
            initial_query=rag_query,
            max_loops=4,
            k_per_step=max(5, k),  # ensure at least a few per step
            debug=debug,
        )
        context = build_context(results)
    except Exception:
        logger.exception(
            "Retrieval (RCR) failed for query='%s' (rewritten='%s')",
            query,
            rag_query,
        )
        return (
            "Sorry, I ran into a problem looking up the Pokémon data. "
            "Please try again in a moment."
        )

    if debug:
        try:
            print("\n================== RCR TRACE ==================\n")
            print(json.dumps(rcr_trace, indent=2, ensure_ascii=False))
        except Exception:
            pass

    prompt = f"""You are a helpful Pokédex assistant for all generations of Pokémon.
Use ONLY the provided context when answering – if the context does not contain
the answer, say you don't know.

Conversation so far:
{convo or "(no previous conversation)"}

Context:
{context or "(no relevant context was found in the knowledge base)"}

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
