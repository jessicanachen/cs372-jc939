import json
import faiss
import os
import logging
from sentence_transformers import SentenceTransformer
from openai import OpenAI
from pathlib import Path
from dotenv import load_dotenv

from .chatbot_utils.utils import trim_history, format_history, build_context, extract_search_query
from .chatbot_utils.prompt_provider import make_rewrite_with_history_prompt, make_sufficiency_prompt, make_refinement_prompt, make_answer_prompt

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


def rewrite_query_with_history(query, history, debug: bool = False):
    '''
    First chatbot, rewrites query with context to be input into RAG.
    '''
    if history is None:
        history = []

    history = trim_history(history)
    convo = format_history(history)

    prompt = make_rewrite_with_history_prompt(convo, query)

    try:
        logger.debug("Rewriting query with history")
        response = client.responses.create(
            model="gpt-4.1-mini",
            input=prompt,
        )
        rewritten = response.output_text.strip()
        logger.info("Rewrote query for retrieval: %s", rewritten)
        return rewritten
    except Exception:
        logger.exception("Error while rewriting query; falling back to original query")
        return query

def sufficiency(query, context, debug: bool = False):
    suff_prompt = make_sufficiency_prompt(query, context)

    try:
        suff_resp = client.responses.create(
            model="gpt-4.1-mini",
            input=suff_prompt,
        )
        suff_text = (suff_resp.output_text or "").strip()
    except Exception:
        logger.exception("RCR: sufficiency check failed")

    logger.debug("RCR sufficiency response: %s", suff_text)

    upper = suff_text.upper()
    if upper.startswith("YES"):
        return True

    return False

def refinement(context, current_query, debug):
    refine_prompt = make_refinement_prompt(context, current_query)

    try:
        refine_resp = client.responses.create(
            model="gpt-4.1-mini",
            input=refine_prompt,
        )
        return (refine_resp.output_text or "").strip()
    except Exception:
        logger.exception("RCR: refinement step failed")

def answer(context, query, debug):
    prompt = make_answer_prompt(context, query)

    print(context)
    try:
        logger.info("Calling OpenAI model for generation")
        response = client.responses.create(
            model="gpt-4.1-mini",
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

def recursive_dense_retrieval(
    query: str,
    max_loops: int = 4,
    k: int = 8,
    debug: bool = False,
):
    logger.info(
        "Starting recursive_dense_retrieval for initial_query='%s'",
        query,
    )

    current_query = query

    for loop in range(1, max_loops + 1):
        logger.debug("RCR loop %d with query='%s'", loop, current_query)

        # retrieve chunks
        results = dense_search(
            query=current_query,
            top_k=k,
            debug=debug,
        )

        context = build_context(results)

        logger.debug(
            "RCR loop %d retrieved document results.",
            loop
        )

        print(context)

        sufficient = sufficiency(current_query, context, debug)
        if sufficient: 
            logger.info(
                "RCR: stopping at loop %d - model judged context sufficient", loop
            )
            break
        

        refine_text = refinement(context, current_query, debug)
        new_query = extract_search_query(refine_text)

        logger.debug(
            "RCR loop %d refinement -> new query='%s'", loop, new_query
        )

        if not new_query or new_query == current_query:
            logger.info(
                "RCR: refinement did not change the query on loop %d; stopping.", loop
            )
            break

        current_query = new_query

    logger.info(
        "RCR complete:"
    )

    return current_query



def answer_with_rag(query, history=None, k: int = 8, debug: bool = False):
    if history is None:
        history = []

    logger.info("answer_with_rag called with query='%s'", query)

    # Step 1: take context and rewrite query to be a self contained context
    rag_query = rewrite_query_with_history(query=query, history=history)

    # Step 2: try recurse
    try:
        query = recursive_dense_retrieval(
            query=rag_query,
            max_loops=4,
            k=k,
            debug=debug,
        )

        results = dense_search(
            query=query,
            top_k=k,
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

    return answer(context, query, debug)
