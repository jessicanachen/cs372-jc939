# Limitations / Future Improvements

Due to the limited time scale of the project, there is still many avenues of improvement that can be done. While I was not able to fully implement solutions to all the issues I would like to acknowledge them, explain the cause, and in the future what can be fixed. 

The biggest issue right now is simple retrieval matching through semantics is not enough to guarantee retrieval of the correct document. This is simply due to the skewed nature of the dataset. Pokemon moves takes up a predominant chunk of the embeddings, causing information adjacent to pokemon moves to not be fetched. The best way to address this is to create a FAISS embedding for the general types of information (what pokemon has what moves, what are the moves powers, etc...), and then create an orchestrator on top that selects which of the indeces has the cunk based on what the question needs. 

[TODO] maybe going into more depth make this better