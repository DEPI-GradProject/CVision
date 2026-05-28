# utils/retriever.py

import os
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_classic.retrievers import EnsembleRetriever, ContextualCompressionRetriever
from langchain_community.retrievers import BM25Retriever
from langchain_community.cross_encoders import HuggingFaceCrossEncoder
from langchain_classic.retrievers.document_compressors import CrossEncoderReranker
# Path to the local FAISS database
FAISS_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "faiss_db")

# Globals to load models into memory only once (for performance optimization)
_embeddings = None
_vectorstore = None
_advanced_retriever = None

def get_embeddings():
    """Load the Embeddings model to convert text into vectors."""
    global _embeddings
    if _embeddings is None:
        _embeddings = HuggingFaceEmbeddings(
            model_name="BAAI/bge-small-en-v1.5"
        )
    return _embeddings

def get_vectorstore():
    """Load the FAISS vector database from local storage."""
    global _vectorstore
    if _vectorstore is None:
        _vectorstore = FAISS.load_local(
            FAISS_PATH,
            get_embeddings(),
            allow_dangerous_deserialization=True
        )
    return _vectorstore

def get_advanced_retriever(k: int = 5):
    """
    Build the search engine using Fast Hybrid Search (without slow reranking).
    """
    global _advanced_retriever
    
    if _advanced_retriever is None:
        vectorstore = get_vectorstore()
        
        # A. Semantic Search (Vector)
        faiss_retriever = vectorstore.as_retriever(
            search_type="similarity", 
            search_kwargs={'k': k}
        )
        
        # B. Keyword Search (BM25)
        docs = list(vectorstore.docstore._dict.values())
        bm25_retriever = BM25Retriever.from_documents(docs)
        bm25_retriever.k = k
        
        # C. Ensemble (Hybrid) Retriever
        _advanced_retriever = EnsembleRetriever(
            retrievers=[faiss_retriever, bm25_retriever],
            weights=[0.5, 0.5]
        )
        
    # Dynamically update the final number of jobs
    _advanced_retriever.retrievers[0].search_kwargs['k'] = k
    _advanced_retriever.retrievers[1].k = k
    
    return _advanced_retriever

def search_jobs(query: str, k: int = 5):
    """
    Main function called by the Agent to search for jobs.
    """
    retriever = get_advanced_retriever(k=k)
    
    # Execution flow: Hybrid Search -> Fetch 15 -> Rerank -> Return top k jobs
    results = retriever.invoke(query)
    
    jobs = []
    for doc in results:
        jobs.append({
            "title": doc.metadata.get("title", "Unknown Title"),
            "link": doc.metadata.get("link", "#"),
            "price": doc.metadata.get("price", "N/A"),
            "skills": doc.metadata.get("skills", "")
        })
    
    return jobs