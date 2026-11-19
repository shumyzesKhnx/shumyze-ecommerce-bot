
import json
from pathlib import Path

import chromadb
from chromadb.utils.embedding_functions import DefaultEmbeddingFunction


# Project paths
BASE_DIR = Path(__file__).resolve().parent
FAQ_FILE = BASE_DIR / "faqs.json"
DB_DIR = BASE_DIR / "chroma_db"

# Initialize ChromaDB
client = chromadb.PersistentClient(path=str(DB_DIR))

# Initialize embedding function
embedding_function = DefaultEmbeddingFunction()

# Create or access FAQ collection
collection = client.get_or_create_collection(
    name="shopmate_faqs",
    embedding_function=embedding_function,
    metadata={"hnsw:space": "cosine"}
)


def ingest_faqs():
    # Load FAQ data
    with open(FAQ_FILE, "r", encoding="utf-8") as file:
        faqs = json.load(file)

    # Prepare data for ChromaDB
    ids = [faq["id"] for faq in faqs]
    documents = [faq["question"] for faq in faqs]

    metadatas = [
        {
            "answer": faq["answer"],
            "category": faq["category"]
        }
        for faq in faqs
    ]

    # Store FAQs and generate embeddings
    collection.upsert(
        ids=ids,
        documents=documents,
        metadatas=metadatas
    )

    print(f"Successfully ingested {len(faqs)} FAQs.")
    print(f"Total FAQs in database: {collection.count()}")


def search_faq(query, n_results=3):
    # Check whether the collection contains data
    total = collection.count()

    if total == 0:
        return []

    # Search for relevant FAQs
    results = collection.query(
        query_texts=[query],
        n_results=min(n_results, total),
        include=["metadatas", "distances", "documents"]
    )

    matches = []

    for metadata, distance in zip(
        results["metadatas"][0],
        results["distances"][0]
    ):
        # Lower cosine distance means greater similarity
        if distance <= 0.65:
            matches.append({
                "category": metadata["category"],
                "answer": metadata["answer"],
                "distance": distance
            })

    return matches


if __name__ == "__main__":
    ingest_faqs()
    print("\nTesting FAQ retrieval...")

    test_query = "How do I get my money back?"
    results = search_faq(test_query)

    for item in results:
        print("\nCategory:", item["category"])
        print("Answer:", item["answer"])
        print("Distance:", item["distance"])

