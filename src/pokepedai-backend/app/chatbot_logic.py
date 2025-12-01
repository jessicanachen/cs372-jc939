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
            model="gpt-4.1-mini",
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
        suff_prompt = f"""<task>
Decide if the Context below is enough, by itself, to fully and specifically answer
a Pokémon-related question from a Pokédex knowledge base.
</task>

<question>
{original_question}
</question>

<context>
{partial_context or "(no context yet)"}
</context>

<what_sufficient_means>
- "Sufficient" means you could write a clear, detailed, and factually correct answer
  using ONLY the Context and NO outside knowledge.
- If the question has multiple parts (e.g., several moves, stats, versions, or conditions),
  the Context must clearly cover ALL important parts.
- If any important part of the question is missing, vague, contradictory, or only hinted at,
  treat the Context as NOT sufficient.
- When in doubt, choose NOT sufficient.
</what_sufficient_means>

<examples>
Example 1:
Q: What type is Bulbasaur?
Context: "Bulbasaur is a Grass/Poison-type Pokémon."
→ Sufficient? YES

Example 2:
Q: What moves does Bulbasaur learn by level up?
Context: "Bulbasaur learns Tackle and Growl."
→ Sufficient? NO (the question implies the full learnset, but only two moves are given)

Example 3:
Q: What is the PP of Hyper Beam?
Context: "Hyper Beam has 150 base power."
→ Sufficient? NO (PP is not given)
</examples>

<output_instructions>
Answer with EXACTLY one word on its own line:
- YES  -> Context is clearly sufficient to fully and specifically answer the question.
- NO   -> More information could help, or you are unsure.

Do NOT include any other words, symbols, or explanation.
</output_instructions>
"""

        try:
            suff_resp = client.responses.create(
                model="gpt-4.1-mini",
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
        refine_prompt = f"""<task>
You are the recursive retrieval planner for a Pokédex knowledge base.
At each loop, your job is to:
1) Immediately process what we already know from the Context, and
2) Deep-dive by producing a sharper search query that asks ONLY for the
   missing information we still need.
</task>

<original_question>
{original_question}
</original_question>

<context>
{partial_context or "(no context yet)"}
</context>

<current_query>
{current_query}
</current_query>

<rules_common>
- You are NOT answering the user yet; you are shaping the next retrieval query.
- Use ONLY the Context above to resolve vague phrases (e.g. "its first move",
  "that move", "this ability", "level 1 move", "that Grass attack").
- Do NOT invent any new factual Pokémon information that is not clearly stated
  in the Context (no guessing move names, PP, power, types, or generations).
- Always keep the core intent of the original question the same
  (e.g., still about PP, base power, accuracy, learnset, evolution, etc.).
- Prefer making the query more specific about the entity and property we care
  about instead of broader.
- If the Context is basically empty or irrelevant, then leave the question
  mostly unchanged and just make it a clean, retrieval-friendly query.
</rules_common>

<immediate_processing>
Your first job is IMMEDIATE PROCESSING over the current Context:

- Identify which parts of the original question can already be concretely
  resolved from the Context.
  Examples:
  * "Bulbasaur's first move" → "Tackle" if the Context clearly shows Tackle as
    the level 1 / first learned move.
  * "its Grass attack" → "Vine Whip" if the Context links that phrase to Vine Whip.
  * "level 1 move" → specific move names if the Context lists them.
- For each such resolvable phrase, mentally rewrite the question to replace
  the vague phrase with the specific name(s) from the Context.
- This internal rewrite is IMMEDIATE PROCESSING of the current knowledge:
  you are partially answering the question only to make the retrieval query
  more precise. Do NOT output this intermediate reasoning; just use it to
  shape the final QUERY.
</immediate_processing>

<deep_dive_planning>
Your second job is to plan a DEEP DIVE retrieval step:

- After immediate processing, ask: “What information is STILL missing from
  the Context to fully answer the original question?”
  Examples:
  * We now know the move is Tackle, but the PP is not listed → we need Tackle’s PP.
  * We know Bulbasaur’s level 1 moves in Red/Blue, but not in Gold/Silver
    → we need level-up moves in Gold/Silver.
- The next search query should:
  * Focus on the still-missing property (PP, base power, accuracy, full list
    of moves, generation-specific info, etc.).
  * Include any concrete names you resolved during immediate processing
    (Pokémon names, move names, abilities, game versions, generations).
  * Stay anchored to the original question’s intent instead of wandering
    to unrelated concepts.
</deep_dive_planning>

<examples>
Example 1 — "first move" PP
[Original Question]
What is Bulbasaur's first move's PP?

[Context]
Bulbasaur learns the following moves by level up in Pokémon Red & Blue:
Level 1: Tackle (PP 35)
Level 3: Growl (PP 40)

[Immediate Processing]
- "first move" can be resolved as the move "Tackle" (Lv. 1) from the Context.

[Deep Dive Planning]
- Missing info: We specifically care about the PP of Tackle.
- Next query should directly ask for the PP of Tackle as Bulbasaur's level 1 move.

[Output]
Replaced "first move" with "Tackle (Bulbasaur's level 1 move in Pokémon Red & Blue)".
QUERY: What is the PP of Bulbasaur's move Tackle (Lv. 1) in Pokémon Red & Blue?

Example 2 — ambiguous pronoun
[Original Question]
How strong is its Grass attack?

[Context]
Bulbasaur learns Vine Whip, a Grass-type move with 45 base power.

[Immediate Processing]
- "its Grass attack" can be resolved as "Vine Whip (a Grass-type move)".

[Deep Dive Planning]
- Missing info: we want the base power explicitly.

[Output]
Replaced "its Grass attack" with "the Grass-type move Vine Whip".
QUERY: What is the base power of Bulbasaur's Grass-type move Vine Whip?

Example 3 — nothing resolvable yet
[Original Question]
What moves does MissingNo. learn in Emerald?

[Context]
Bulbasaur is a Grass/Poison-type Pokémon. It learns Tackle and Growl.
No information about MissingNo. or Pokémon Emerald is provided.

[Immediate Processing]
- Nothing about MissingNo. or Emerald can be resolved from the Context.

[Deep Dive Planning]
- We still need information about MissingNo.'s moves in Emerald, but we have
  no guidance from Context, so we keep the query essentially the same.

[Output]
No changes; not enough information to rewrite the question.
QUERY: What moves does MissingNo. learn in Pokémon Emerald?
</examples>

<output_format>
Produce exactly TWO lines:

1) First line:
   - A short sentence describing what you changed, OR
   - "No changes; not enough information to rewrite the question."
2) Second line:
   - Start with 'QUERY: ' and then write the refined search question.
   - If no changes were made, still include the original question after 'QUERY: '.

Do NOT include any other lines, explanations, or XML tags.
</output_format>
"""

        try:
            refine_resp = client.responses.create(
                model="gpt-4.1-mini",
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
        context = build_context(results, )
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

    prompt = f"""<assistant_role>
You are a Pokédex-style assistant that answers questions about all generations of official Pokémon games.
Your primary job is to read the provided Context and answer questions about Pokémon, moves, abilities, and related mechanics.
</assistant_role>

<grounding_rules>
- Treat the text inside the <context> tag as the ONLY authoritative Pokémon knowledge you can use.
- Never invent or guess numbers, names, move effects, stats, or mechanics that are not supported by the Context.
- If the Context does not contain the answer, or it is not clear enough to answer with high confidence, clearly say you don't know based on the provided context.
- If the Context contains conflicting information, say that the sources disagree and prefer information that appears associated with later generations or more specific details.
- Do not mention the words "context", "chunks", "embeddings", or "vector store" in your final answer.
</grounding_rules>

<input>
  <conversation_history>
  {convo or "(no previous conversation)"}
  </conversation_history>

  <context>
  {context or "(no relevant context was found in the knowledge base)"}
  </context>

  <question>
  {query}
  </question>
</input>

<reasoning_guidelines>
- Step 1: Identify the main entities in the question (e.g., Pokémon name, move name, ability name, item, generation, game).
- Step 2: Look through the Context for sentences that clearly reference those entities.
- Step 3: Combine matching pieces of information, ignoring text about unrelated Pokémon or moves.
- Step 4: If multiple generations or games are mentioned:
  - If the user specified a generation or game, focus on that.
  - If not specified, either summarize across all relevant generations/games or clearly state which generation(s) your answer is based on.
- Step 5: If you still cannot answer confidently using only the Context, say that you don't know based on the provided context.
</reasoning_guidelines>

<response_style>
- Answer in plain text only. Do NOT include any XML tags in your answer.
- Default to a single concise paragraph of 2-5 sentences.
- Include specific numbers, names, move names, types, abilities, levels, and conditions whenever the Context provides them.
- If the user explicitly asks for lists, tables, comparisons, or step-by-step instructions, follow their requested format instead of a single paragraph.
- When listing moves a Pokémon learns, prefer giving both move names and their levels (when available in the Context).
- Be explicit about which generation or game your answer applies to when the Context makes that clear.
</response_style>

<behavior_when_missing_info>
- If the Context is empty or clearly unrelated to the question, say something like:
  "I don't know based on the provided context."
- Optionally, you may briefly suggest what extra detail would help (e.g., specifying a generation or game), but do NOT add any new factual Pokémon information not present in the Context.
</behavior_when_missing_info>

<examples>
  <example id="1">
    <user_question>
    What moves does Bulbasaur learn?
    </user_question>

    <example_context>
    Bulbasaur is a Grass/Poison-type Pokémon introduced in Generation 1.
    In Pokémon Red, Blue and Yellow, Bulbasaur learns the following moves by leveling up:
    Level 1: Tackle
    Level 3: Growl
    Level 7: Leech Seed
    Level 13: Vine Whip
    Level 20: Poison Powder
    Level 27: Razor Leaf
    Level 34: Growth
    Level 41: Solar Beam.
    In later games, Bulbasaur can also learn additional moves via TMs and tutors, but those are not listed here.
    </example_context>

    <ideal_answer>
    Based on the provided context, Bulbasaur learns Tackle (Lv. 1), Growl (Lv. 3), Leech Seed (Lv. 7),
    Vine Whip (Lv. 13), Poison Powder (Lv. 20), Razor Leaf (Lv. 27), Growth (Lv. 34), and Solar Beam (Lv. 41)
    by leveling up in Pokémon Red, Blue, and Yellow. The context also mentions that Bulbasaur can learn
    additional moves through TMs and tutors, but those moves and levels are not specified here.
    </ideal_answer>
  </example>

  <example id="2">
    <user_question>
    Give me the details on Hyper Beam.
    </user_question>

    <example_context>
    Hyper Beam is a Normal-type Special move introduced in Generation 1.
    It has 150 base power, 90% accuracy, and 5 PP.
    After using Hyper Beam, the user must recharge on the next turn and cannot act during that turn.
    </example_context>

    <ideal_answer>
    According to the provided context, Hyper Beam is a Normal-type Special move introduced in Generation 1.
    It has 150 base power, 90% accuracy, and 5 PP. After using Hyper Beam, the user must spend the next turn
    recharging and cannot act, which is the main drawback of the move.
    </ideal_answer>
  </example>

  <example id="3">
    <user_question>
    What does the ability Static do?
    </user_question>

    <example_context>
    Pikachu Pokémon have the ability Static.
    This ability was introduced in generation 3.
    Static may cause paralysis when an opposing Pokémon makes contact with the Pokémon that has this ability.
    </example_context>

    <ideal_answer>
    Based on the context, Static is an ability (introduced in Generation 3) that can cause paralysis when
    an opposing Pokémon makes contact with the Pokémon that has Static. In other words, physical contact
    moves against a Pokémon with Static have a chance to leave the attacker paralyzed.
    </ideal_answer>
  </example>

  <example id="4">
    <user_question>
    What moves does MissingNo. learn in Emerald?
    </user_question>

    <example_context>
    Bulbasaur is a Grass/Poison-type Pokémon introduced in Generation 1.
    Bulbasaur learns moves such as Tackle, Growl, Leech Seed, and Vine Whip in Generation 1 games.
    No information about MissingNo. or Pokémon Emerald is provided here.
    </example_context>

    <ideal_answer>
    I don't know based on the provided context. The context only describes Bulbasaur's moves in
    Generation 1 and does not contain any information about MissingNo. or Pokémon Emerald.
    </ideal_answer>
  </example>
</examples>

<final_instruction>
Using the <grounding_rules>, <reasoning_guidelines>, and <response_style> above,
answer the <question> using ONLY the information inside <context>.
Your output must be just the final answer in plain text, with no XML tags.
</final_instruction>
    """

    print("\n================== CONTEXT USED ==================\n")
    print(context)

    print("\n================== HISTORY ==================\n")
    print(convo)

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
