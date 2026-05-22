from Backend_sandbox.data_loader import load_website
from Backend_sandbox.rag_pipeline import split_docs, add_to_vectorstore

docs = load_website()
chunks = split_docs(docs)
add_to_vectorstore(chunks)

print("Vector DB ready and synchronized with RAG pipeline!")
