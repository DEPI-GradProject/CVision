import re

import pandas as pd
from sqlalchemy import create_engine, text

from config import settings

engine = create_engine(settings.database_url_with_ssl)

ALLOWED_TABLES = {"training_jobs", "jobs_raw"}


# --- 2. Text Cleaning Function ---
def clean_text(text):
    if pd.isna(text):
        return "No Description"
    text = str(text)

    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"http\S+", " ", text)
    text = re.sub(r"[\n\t\r]", " ", text)
    text = re.sub(r"\s+", " ", text)

    return text.strip()


# --- 3. Pipeline Function ---
def clean_table(table_name, desc_column):
    if table_name not in ALLOWED_TABLES:
        print(f"❌ Table '{table_name}' is not in the allowed list.")
        return

    print(f"\n[{table_name}] Fetching data from database...")
    try:
        df = pd.read_sql(text(f"SELECT * FROM {table_name}"), engine)
        print(f"[{table_name}] Found {len(df)} rows. Cleaning text in '{desc_column}' column...")

        df[desc_column] = df[desc_column].apply(clean_text)

        print(f"[{table_name}] Uploading clean data back to database...")
        with engine.begin() as conn:
            conn.execute(text(f"DELETE FROM {table_name}"))
            df.to_sql(table_name, conn, if_exists="append", index=False)
        print(f"[{table_name}] Cleaned and updated successfully!")

    except Exception as e:
        print(f"Error with table {table_name}: {e}")


if __name__ == "__main__":
    print("Starting Data Cleaning Pipeline...")

    clean_table("training_jobs", "Description")
    clean_table("jobs_raw", "description")

    print("\nAll data is now squeaky clean and ready for the AI Model!")
