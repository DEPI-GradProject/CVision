# utils/retriever.py

import os
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings

FAISS_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "faiss_db")

_embeddings = None
_vectorstore = None

def get_embeddings():
    global _embeddings
    if _embeddings is None:
        _embeddings = HuggingFaceEmbeddings(
            model_name="BAAI/bge-small-en-v1.5"
        )
    return _embeddings

def get_vectorstore():
    global _vectorstore
    if _vectorstore is None:
        _vectorstore = FAISS.load_local(
            FAISS_PATH,
            get_embeddings(),
            allow_dangerous_deserialization=True
        )
    return _vectorstore

def search_jobs(query: str, k: int = 5):
    vectorstore = get_vectorstore()
    results = vectorstore.similarity_search(query, k=k)
    
    jobs = []
    for doc in results:
        jobs.append({
            "title": doc.metadata["title"],
            "link": doc.metadata["link"],
            "price": doc.metadata["price"],
            "skills": doc.metadata["skills"]
        })
    
    return jobs