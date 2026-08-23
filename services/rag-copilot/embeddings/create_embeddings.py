import os
import pickle
import faiss
from sentence_transformers import SentenceTransformer

KNOWLEDGE_BASE = "knowledge_base"

documents = []

# Load all markdown files
for filename in os.listdir(KNOWLEDGE_BASE):
    if filename.endswith(".md"):
        filepath = os.path.join(KNOWLEDGE_BASE, filename)

        with open(filepath, "r", encoding="utf-8") as file:
            content = file.read()
            documents.append({
                "filename": filename,
                "content": content
            })

print(f"Loaded {len(documents)} documents.")

# Load embedding model
model = SentenceTransformer("all-MiniLM-L6-v2")

# Create embeddings
texts = [doc["content"] for doc in documents]
embeddings = model.encode(texts)

# Create FAISS index
dimension = embeddings.shape[1]
index = faiss.IndexFlatL2(dimension)
index.add(embeddings)

# Save vector database
os.makedirs("vector_db", exist_ok=True)

faiss.write_index(index, "vector_db/security_index.faiss")

with open("vector_db/documents.pkl", "wb") as f:
    pickle.dump(documents, f)

print("✅ Vector database created successfully!")
print(f"Indexed {len(documents)} documents.")