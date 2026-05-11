import os

import pandas as pd
from sqlalchemy import create_engine

from config import settings

engine = create_engine(settings.database_url_with_ssl)

print("Reading Excel files from 'Data' folder...")

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Data")

try:
    freelancer_df = pd.read_excel(os.path.join(DATA_DIR, "Freelancer_data.xlsx"))
    guru_df = pd.read_excel(os.path.join(DATA_DIR, "Guru_data.xlsx"))
    upwork_df = pd.read_excel(os.path.join(DATA_DIR, "UPWork_data.xlsx"))

    # add a new column to identify the source platform for each job
    freelancer_df["platform_source"] = "Freelancer"
    guru_df["platform_source"] = "Guru"
    upwork_df["platform_source"] = "Upwork"

    # --- 3. Combine Data ---
    # mix all the dataframes into one big dataframe (ignore_index=True so it resets the index)
    all_jobs_df = pd.concat([freelancer_df, guru_df, upwork_df], ignore_index=True)

    print(f"Total jobs to upload: {len(all_jobs_df)}")
    print("Uploading to database table 'training_jobs'... This might take a minute ⏳")

    # --- 4. Upload to Database ---
    # upload the combined dataframe to the 'training_jobs' table in the database
    all_jobs_df.to_sql("training_jobs", engine, if_exists="append", index=False)

    print("\n✅ Success! All training data has been uploaded to the 'training_jobs' table.")

except FileNotFoundError as e:
    print(f"❌ Error: Could not find the file. Make sure you moved the files to the 'data' folder! ({e})")
except Exception as e:
    print(f"❌ An error occurred: {e}")
