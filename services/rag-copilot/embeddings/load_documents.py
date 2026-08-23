import os

KNOWLEDGE_BASE = "knowledge_base"

documents = []

for filename in os.listdir(KNOWLEDGE_BASE):
    if filename.endswith(".md"):
        filepath = os.path.join(KNOWLEDGE_BASE, filename)

        with open(filepath, "r", encoding="utf-8") as file:
            content = file.read()

            documents.append({
                "filename": filename,
                "content": content
            })

print(f"Loaded {len(documents)} documents.\n")

for doc in documents:
    print("=" * 60)
    print(f"File: {doc['filename']}")
    print(doc["content"][:200])  # Preview first 200 characters
    print()