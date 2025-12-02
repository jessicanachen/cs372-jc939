# Data Set Creations Documentation

## RAG Chunks

The first dataset that needs to be created are the ones used in RAG retrieval. The first step in construction is determining what data needs to be included, and where the information can be retrieved. 

### Dataset Design Choices

**Where to Collect Info**

So, considering the goal of PokepedAI is to serve as a chatbot one can use when playing Pokemon games, we can use a common source of information players typically use to get this infomation [PokemonDB](
https://pokemondb.net)

**What Info Should Be Collected**

PokemonDB contains a lot of information overall about Pokemon but included in the documents will be information for the most common questions people will ask:

```
What type is <Pokemon>?
What are the base stats of <Pokemon>?
How does <Pokemon A> compare to <Pokemon B>?

How do I evolve <Pokemon>?
What level does <Pokemon> evolve?
What can <Pokemon> evolve into?

What abilities does <Pokemon> have?
What is <Pokemon>'s hidden ability?
Which Pokemon have <Ability>?
What does <Ability> do?

What moves does <Pokemon> learn by level-up?
What TMs can <Pokemon> learn?
Can <Pokemon> learn <Move>?
Which Pokemon can learn <Move>?
When does <Pokemon> learn <Move>?

What are <Pokemon>'s weaknesses?
What is super effective against <Pokemon>?
Which Pokemon resist <Type>?

Where can I find <Pokemon> in <Game>?
Which Pokemon appear in <Location> in <Game>?
Which Pokemon are version exclusives in <Game>?

What egg group is <Pokemon>?
Which Pokemon share an egg group with <Pokemon>?
Can <Pokemon> breed?
```

Thus the main parts of the website we wanted to scrape were information and stats specific to a Pokemon, abilities, moves, and other gameplay mechanics such as breeding, IVs, EVs...

**RAG Chunks Format**

The last major choice when it came to creating the data is how we decided to store the information.

While creating this dataset, especially for Pokemon specific information, since much of it is organized into tables and charts, which does not translate well into a RAG (which likes natural language styled documents), we will convert such information into a natural language text while keeping the raw information as metadata instead of just directly inserting the text of the scraped website to the RAG.

In addition, to help with indexing, all information will be split into smaller json sections based on the information they hold. Since this document is mostly consistent of fact based information (Pokemon move stats, Pokemon stats) that does not rely too much on broader context, these RAG chunks will be broken into small sections in order for more granualer indexes. 

There are 3 main formats for one of these chunks:
```json
// Specific to Pokemon Info
{"id": "Bulbasaur-core", "pokemon": "Bulbasaur", "section": "core", "text": "Bulbasaur is a Grass/Poison-type Pokémon introduced in Generation 1. It is number 1 in the National Pokédex. Bulbasaur is classified as the Seed Pokémon. Bulbasaur is 0.7 m (2′04″) tall and weighs 6.9 kg (15.2 lbs).", "metadata": {"National Dex Number": 1, "Types": ["Grass", "Poison"], "Generatin": 1, "Species": "Seed", "Height": "0.7 m (2′04″)", "Weight": "6.9 kg (15.2 lbs)"}}

// Moves Info
{"id": "move-apple-acid-gen8", "section": "moves-by-generation", "text": "Apple Acid is a Grass-type Special move introduced in Generation 8. It has base power 80, accuracy 100, PP 10. Lowers target's Special Defense.", "metadata": {"generation": 8, "move_name": "Apple Acid", "move_slug": "apple-acid", "type": "Grass", "category": "Special", "power": "80", "accuracy": "100", "pp": "10", "effect": "Lowers target's Special Defense."}}

// General Info
{"id": "abilities-overview", "section": "abilities", "text": "Abilities are special attributes given to each Pokémon that can aid them in battle. Many abilities act as a power-up by increasing a move or stat; others introduce a third-party effect like a weather condition. Some abilities can even hinder a Pokémon battle.", "metadata": {"name": "Abilities"}}
```

### Dataset Creation Methodology

For the most part, information was web scraped, cleaned, and then automatically created using the script found [here](../notebooks/PokemonScraper.ipynb). This was done by using BeautifulSoup to get the raw html of the necessary page, then traversing the DOM structure to retrieve the information. This information was then converted to a standard natural language form and built into the RAG chunks as described above.

However, in the case of game mechanic information as well as the type matchups charts, due to the nature of the game mechanic information being text not formated in a standard manner as other urls (aka if I made a dom element retrieval for these pages, I would have to make a unique one for each ones), these RAG chunks were made manually without a script.


## Fine Tuning Data

The second data set that needs to be created are those used to fine tune the mode.

[TODO]