import json
import faiss
import os
import logging
from sentence_transformers import SentenceTransformer
from openai import OpenAI
from pathlib import Path
from dotenv import load_dotenv

from .chatbot_utils.utils import (
    trim_history,
    format_history,
    build_context,
    extract_search_query,
)
from .chatbot_utils.prompt_provider import (
    make_rewrite_with_history_prompt,
    make_sufficiency_prompt,
    make_refinement_prompt,
    make_answer_prompt,
)

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


def dense_search(query, top_k: int = 50, debug: bool = False):
    """
    Return top k document matches with RAG retrieval.
    """
    logger.info("[STEP] dense_search | query='%s'", query)

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
                "[DEBUG] DENSE #%d | idx=%d | score=%.4f | [%s — %s] %s%s",
                rank,
                idx,
                score,
                pokemon,
                section,
                text[:300].replace("\n", " "),
                "... [truncated]" if len(text) > 300 else "",
            )

    return results


def rewrite_query_with_history(query, history, debug: bool = False):
    """
    First chatbot, rewrites query with context to be input into RAG.
    """
    logger.info("[STEP] rewrite_query_with_history | query='%s'", query)

    if history is None:
        history = []

    history = trim_history(history)
    convo = format_history(history)

    prompt = make_rewrite_with_history_prompt(convo, query)

    try:
        response = client.responses.create(
            model="gpt-4.1-mini",
            input=prompt,
        )
        rewritten = (response.output_text or "").strip()
        logger.info(
            "[STEP] rewrite_query_with_history_done | rewritten_query='%s'", rewritten
        )
        if debug:
            logger.debug(
                "[DEBUG] rewrite_query_with_history | original='%s' rewritten='%s'",
                query,
                rewritten,
            )
        return rewritten
    except Exception:
        logger.exception(
            "Error while rewriting query; falling back to original query"
        )
        return query


def sufficiency(query, context, debug: bool = False):
    """
    Ask the model if the current context is sufficient to answer the query.
    """
    logger.info("[STEP] sufficiency_check | query='%s'", query)

    suff_prompt = make_sufficiency_prompt(query, context)
    suff_text = ""

    try:
        suff_resp = client.responses.create(
            model="gpt-4.1-mini",
            input=suff_prompt,
        )
        suff_text = (suff_resp.output_text or "").strip()
    except Exception:
        logger.exception("RCR: sufficiency check failed")
        # If sufficiency check fails, treat as not sufficient so we keep looping.
        return False

    if debug:
        logger.debug(
            "[DEBUG] sufficiency_check | query='%s' response='%s'",
            query,
            suff_text,
        )

    upper = suff_text.upper()
    if upper.startswith("YES"):
        return True

    return False


def refinement(context, current_query, debug: bool = False):
    """
    Ask the model how to refine the search query given the current context.
    """
    logger.info("[STEP] refinement | query='%s'", current_query)

    refine_prompt = make_refinement_prompt(context, current_query)

    try:
        refine_resp = client.responses.create(
            model="gpt-4.1-mini",
            input=refine_prompt,
        )
        refine_text = (refine_resp.output_text or "").strip()

        if debug:
            logger.debug(
                "[DEBUG] refinement | current_query='%s' refine_text='%s'",
                current_query,
                refine_text,
            )

        return refine_text
    except Exception:
        logger.exception("RCR: refinement step failed")
        return None


def answer(context, query, debug: bool = False):
    """
    Final answer generation using the retrieved context.
    """
    logger.info("[STEP] answer_generation | query='%s'", query)

    if debug:
        logger.debug("[DEBUG] answer_generation context: %s", context)

    prompt = make_answer_prompt(context, query)

    try:
        response = client.responses.create(
            model="gpt-4.1-mini",
            input=prompt,
        )
        reply = response.output_text
        logger.info("[STEP] answer_generation_done | query='%s'", query)
        return reply
    except Exception:
        logger.exception("OpenAI generation failed")
        return (
            "Sorry, I had an internal error while generating this answer. "
            "Please try again shortly."
        )


def recursive_dense_retrieval(
    query: str,
    max_loops: int = 4,
    k: int = 8,
    debug: bool = False,
):
    logger.info("[STEP] RCR_start | initial_query='%s'", query)

    current_query = query

    for loop in range(1, max_loops + 1):
        logger.info(
            "[STEP] RCR_loop | loop=%d | query='%s'",
            loop,
            current_query,
        )

        # retrieve chunks
        results = dense_search(
            query=current_query,
            top_k=k,
            debug=debug,
        )

        context = build_context(results)

        if debug:
            logger.debug(
                "[DEBUG] RCR_loop | loop=%d | context=%s",
                loop,
                context,
            )

        sufficient = sufficiency(current_query, context, debug)
        if sufficient:
            logger.info(
                "[STEP] RCR_stop_sufficient | loop=%d | query='%s'",
                loop,
                current_query,
            )
            break

        refine_text = refinement(context, current_query, debug)
        new_query = extract_search_query(refine_text)

        if debug:
            logger.debug(
                "[DEBUG] RCR_refinement_result | loop=%d | new_query='%s'",
                loop,
                new_query,
            )

        if not new_query or new_query == current_query:
            logger.info(
                "[STEP] RCR_stop_unchanged | loop=%d | query='%s'",
                loop,
                current_query,
            )
            break

        current_query = new_query

    logger.info("[STEP] RCR_complete | final_query='%s'", current_query)

    return current_query


def answer_with_rag(query, history=None, k: int = 8, debug: bool = False):
    if history is None:
        history = []

    logger.info("[STEP] answer_with_rag_start | query='%s'", query)

    # Step 1: take context and rewrite query to be a self contained context
    rag_query = rewrite_query_with_history(query=query, history=history, debug=debug)

    # Step 2: try recursive retrieval
    try:
        final_query = recursive_dense_retrieval(
            query=rag_query,
            max_loops=4,
            k=k,
            debug=debug,
        )

        results = dense_search(
            query=final_query,
            top_k=k,
            debug=debug,
        )

        context = build_context(results)

        if debug:
            logger.debug(
                "[DEBUG] answer_with_rag | final_query='%s' context=%s",
                final_query,
                context,
            )
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

    logger.info("[STEP] answer_with_rag_answer | query='%s'", final_query)
    return answer(context, final_query, debug)
