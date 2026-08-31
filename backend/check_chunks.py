from app.rag.vector_store import VectorStore

store = VectorStore()

results = store.collection.get()

counts = {}

for meta in results["metadatas"]:
    name = meta["document"]
    counts[name] = counts.get(name, 0) + 1

print("\n========== Chunks per PDF ==========\n")

for name, count in sorted(counts.items()):
    print(f"{name} -> {count} chunks")

print("\n====================================")
print("Total PDFs:", len(counts))
print("Total Chunks:", store.collection.count())