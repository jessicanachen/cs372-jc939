# Design Choices

## Central Problem

The central problem that this project is trying to solve is when playing Pokemon games, you often have to stop to find information like where a Pokémon appears, what level it learns a certain move, or what types it’s weak against. This usually requires searching through dozens of wiki pages and databases. This is time-consuming, frustrating, and breaks the flow of playing the game.

Thus, the core design created to solve this problem was to create a RAG system to provide the necessary information and deploy it on a web app so users can easily access it.

### RAG system

The RAG system will provide the information from the wiki pages/databases most people typically use whenever looking up Pokemon information.

In order for the RAG to use this information, the informanation needed to be colleccted and curated. Details about this can be found in [DATASET_CREATION](DATASET_CREATION.md).

Next, once that was created, the chunks were embedded using SentenceTransformers and indexed/stored using the FAISS index. Then to do retrieval for the RAG system, I used the same embedding format and retrieved the top k matches. The choice of using SentenceTransformers and the FAISS index was influenced by my prior RAG work in another project, during that project I determined that SentenceTransformers were better embeddings than using a BERT model as the BERT model due to timing and limitations with a max_token for embedding size. Additionally, including a FAISS index helped speed up retrieval.

However, after implementing the base RAG system, there were a few limitations to the current system. 

The first was if you wanted to ask follow up questions, the system was incapable of answering because it did not know what "it" referred to. To fix this, implemented a multiconversation system. The design choice of only having the query be rewritten and not providing the context in the answer prompt is two fold. In the RAG instead of providing the whole query, the query is first rewritten as if we pass in the entire context and say the user switches from asking questions about bulbasaurs to asking one question about eevee, the retrieval would retrieve documents about bulbasaur only. The decision to not include the history context again in the answer prompt, is it does not take away from the generation too much (except in generation it can't reference past responses), and it saves tokens and thus cost of the project.

The second issue, is cross chunk questions could not be answered. These are questions where the answer of one part of the prompt provides context to another part of the prompt (i.e. what type is bulbasaur super effective against, requires knowing what type bulbasaur is). To solve this, implemented a base recursive RAG system, where if the current chunks are not sufficient to answr the question, the query is rewritten using information from the retrieved chunks and then asked again.

In order to do this (i.e. determing if a prompt is sufficient), used in context learning and chain of thought prompting.

The choice of using a state of the art model, is this way since these models are trained on a lot more data and a lot more parameters than I could do making my own model, and in order to provide the best generation having this higher understanding of word meaning would be helpful, I decided to go with a state of the art model. I chose GPT as I already had API credits in the model.

### Web App

In order for this to complete its goal of being easily accessible, the chatbot was deployed to a web app hosted on Vercel and the backend hosted on Google Cloud. 

To ensure the web app runs smoothly and is not abused, implemented things such as rate limiting, monitoring, and error handling.

In addition, to just conversation history when replying to messages, implemented stored context history. This is as when using Pokepedai, users should be able to easily navigate to past queries and easily organize their sessions for future recall.