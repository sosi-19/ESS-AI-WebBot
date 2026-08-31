from app.rag.retriever import Retriever

retriever = Retriever()

results = retriever.search(
    "What is the Consumer Price Index?"
)

print(results)