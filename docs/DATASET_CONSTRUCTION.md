# Dataset Construction Documentation

First, have to decide where we want to get the base Pokemon information from. Going to use this [site](https://pokemondb.net) as it helps organize the data in pretty consistent and straightforward ways.

Additionally, for pokemon information, there is some code I can use for parsing the html. However, formatting into RAG chunks and also some data they did not parse are my own work

## Pokemon Information

A typical Pokemon information page looks like [this](https://pokemondb.net/pokedex/bulbasaur), however the raw html from this page is not too useful for a RAG system, thus the first point is what format do I want to structure this information in 

### RAG Chunk Per Pokemon


NTS: changes only affect base values, thus somehow parses the changes and put them correctly under stats or training

NTS: Evolution Chart
make sure they oly added once