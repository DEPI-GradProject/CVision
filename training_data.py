import os
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine

# --- 1. Database Connection ---
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
if "sslmode=" not in DATABASE_URL:
    DATABASE_URL += "?sslmode=require"

engine = create_engine(DATABASE_URL)

print("Reading Excel files from 'data' folder...")

try:
    # --- 2. Read Data ---
    freelancer_df = pd.read_excel("data/Freelancer_data.xlsx")
    guru_df = pd.read_excel("data/Guru_data.xlsx")
    upwork_df = pd.read_excel("data/UPWORK_data.xlsx")

    # add a new column to identify the source platform for each job
    freelancer_df['platform_source'] = 'Freelancer'
    guru_df['platform_source'] = 'Guru'
    upwork_df['platform_source'] = 'Upwork'

    # --- 3. Combine Data ---
    # mix all the dataframes into one big dataframe (ignore_index=True so it resets the index)
    all_jobs_df = pd.concat([freelancer_df, guru_df, upwork_df], ignore_index=True)
    
    print(f"Total jobs to upload: {len(all_jobs_df)}")
    print("Uploading to database table 'training_jobs'... This might take a minute ⏳")

    # --- 4. Upload to Database ---
    # upload the combined dataframe to the 'training_jobs' table in the database, replacing it if it already exists
    all_jobs_df.to_sql('training_jobs', engine, if_exists='replace', index=False)
    
    print("\n✅ Success! All training data has been uploaded to the 'training_jobs' table.")

except FileNotFoundError as e:
    print(f"❌ Error: Could not find the file. Make sure you moved the files to the 'data' folder! ({e})")
except Exception as e:
    print(f"❌ An error occurred: {e}")