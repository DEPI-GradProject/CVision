# utils/ingest.py

import pandas as pd
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document

embeddings = HuggingFaceEmbeddings(
    model_name="BAAI/bge-small-en-v1.5"
)

def load_csv_to_faiss(csv_path: str = "Data/jobs.csv"):
    df = pd.read_csv(csv_path)
    
    documents = []
    for _, row in df.iterrows():
        content = f"Title: {row['Title']}\nSkills: {row['Skills']}"
        
        doc = Document(
            page_content=content,
            metadata={
                "title": str(row['Title']),
                "link": str(row['Link']),
                "price": str(row['Price']),
                "skills": str(row['Skills'])
            }
        )
        documents.append(doc)
    
    print(f"Loading {len(documents)} jobs into FAISS...")
    
    vectorstore = FAISS.from_documents(documents, embeddings)
    vectorstore.save_local("data/faiss_db")
    
    print("✅ Done! Jobs loaded into FAISS.")

if __name__ == "__main__":
    load_csv_to_faiss()