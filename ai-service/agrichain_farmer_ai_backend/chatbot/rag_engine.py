from sentence_transformers import SentenceTransformer
import faiss
import os
import numpy as np

model = SentenceTransformer("all-MiniLM-L6-v2")
knowledge_dir = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "knowledge")
)

documents = []
metadata = []

for file in os.listdir(knowledge_dir):
    if not file.endswith(".txt"):
        continue

    file_path = os.path.join(knowledge_dir, file)

    with open(file_path, "r", encoding="utf-8") as f:
        documents.append(f.read())
        metadata.append(file.replace(".txt", ""))

if documents:
    embeddings = model.encode(documents)
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(np.array(embeddings))
else:
    index = None


def retrieve_context(query, role):
    if index is None:
        return ""

    query_embedding = model.encode([query])
    distances, indices = index.search(np.array(query_embedding), k=2)

    contexts = []
    for idx in indices[0]:
        if metadata[idx] == role:
            contexts.append(documents[idx])

    return "\n".join(contexts)