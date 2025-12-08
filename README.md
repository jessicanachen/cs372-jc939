# Pokepedai
*Jessica Chen*

Pokepedai is a natural-language Pokémon chatbot that lets players quickly ask questions about Pokémon and get info from locations, weaknesses, and moves.

## What it Does

In Pokémon games, players run into hundreds of different species, each with their own moves, abilities, types, and unique traits. But often, finding information about them, like where a Pokémon appears, what level it learns a certain move, or what types it’s weak against, usually requires searching through dozens of wiki pages and databases. This is time-consuming, frustrating, and breaks the flow of playing the game. Pokepedai solves this problem by combining this scattered information into a single, easy-to-use source. Instead of manually searching through webpages, players can ask questions in plain language, such as, “Where can I find Bulbasaur?” or “What is Gengar weak to?” Pokepedai interprets these questions and provides clear, accurate answers in one place, making it faster and easier for players to get the info they need and stay focused on enjoying the game.

## Quick Start

To run Pokepedai, simply navigate to [cs372-jc939.vercel.app](https://cs372-jc939.vercel.app). From here, can query the chatbot and interact with the already setup and running project. 

For more detailed information on how to run the project locally consult [SETUP.md](SETUP.md).

## Video Links

- [Demo](/videos/project_demo.mp4)
- [Technical Walkthrough](/videos/technical_walkthrough.mp4)

## Evaluation

Based on the things implemented in this project, there is not much quantitative data to be analyzed, however will go over some of the qualitative evaluations done when making choices for this project.

### Recursive RAG

**Query**

What is bulbasaur super effective against?

**Answer with Base RAG System**

The context states Bulbasaur is a Grass/Poison-type Pokémon, but it does not include any type-effectiveness chart or which types Grass or Poison are super effective against—so I don't know from the provided information.

**Answer with Recursive RAG System**

Grass-type moves are super effective against Water, Ground, and Rock types according to the provided information.

### Rewrite Prompt Improvement

**Old Prompt**

What is the PP of Bulbasaur's first level 1 move?

**Rewrite with Original Rewrite Prompt**

What is the PP of Pokemon Bulbasaur's first level 1 move?

**Rewrite with Final Rewrite Prompt**

What is the PP of Bulbasaur's level 1 move Growl?