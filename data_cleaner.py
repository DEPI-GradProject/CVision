import os
import re
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine

# --- 1. Database Connection ---
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
if "sslmode=" not in DATABASE_URL:
    DATABASE_URL += "?sslmode=require"

engine = create_engine(DATABASE_URL)

# --- 2. Text Cleaning Function ---
def clean_text(text):
    if pd.isna(text):
        return "No Description"
    text = str(text)
    
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'http\S+', ' ', text)
    text = re.sub(r'[\n\t\r]', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    
    return text.strip()

# --- 3. Pipeline Function ---
def clean_table(table_name, desc_column):
    print(f"\n[{table_name}] Fetching data from database...")
    try:
        df = pd.read_sql(f"SELECT * FROM {table_name}", engine)
        print(f"[{table_name}] Found {len(df)} rows. Cleaning text in '{desc_column}' column 🧹...")
        
        #clean the text in the specified description column
        df[desc_column] = df[desc_column].apply(clean_text)
        
        print(f"[{table_name}] Uploading clean data back to database...")
        #upload the cleaned dataframe back to the same table, replacing it
        df.to_sql(table_name, engine, if_exists='replace', index=False)
        print(f"✅ [{table_name}] Cleaned and updated successfully!")
        
    except Exception as e:
        print(f"❌ Error with table {table_name}: {e}")

if __name__ == "__main__":
    print("Starting Data Cleaning Pipeline...")
    
    #clean the training_jobs table first (the one we just uploaded in training_data.py)
    clean_table('training_jobs', 'Description')
    
    #clwean the raw jobs table as well (the one we will use for inference)
    clean_table('jobs_raw', 'description')
    
    print("\n🎉 All data is now squeaky clean and ready for the AI Model!")