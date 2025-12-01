def make_rewrite_with_history_prompt(convo, query):
    return f"""You are a helpful assistant.

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


def make_sufficiency_prompt(original_question, partial_context):
    return f"""<task>
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


def make_refinement_prompt(
    partial_context,
    current_query,
):
    return f"""<task>
You are the recursive retrieval planner for a Pokédex knowledge base.
At each loop, your job is to:
1) Immediately process what we already know from the Context, and
2) Deep-dive by producing a sharper search query that asks ONLY for the
   missing information we still need.
</task>

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


def make_answer_prompt(context, query):
    return f"""<assistant_role>
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
