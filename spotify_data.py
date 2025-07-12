import pandas as pd
import random
from faker import Faker
from uuid import uuid4
from datetime import datetime, timedelta
import os
from multiprocessing import Pool, cpu_count

fake = Faker()

# Output directory for CSVs
OUTPUT_DIR = "./workspace/spotify_data"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Adjust these to control size
RECORDS_PER_CHUNK = 1_000_000     # ~100MB per chunk depending on columns
NUM_CHUNKS = 50                   # 50 chunks ≈ 5GB+

DEVICES = ["mobile", "desktop", "tablet"]

def generate_record():
    return {
        "user_id": str(uuid4()),
        "song_id": str(uuid4()),
        "artist_id": str(uuid4()),
        "timestamp": fake.date_time_between(start_date='-1y', end_date='now'),
        "duration_ms": random.randint(60_000, 300_000),
        "device": random.choice(DEVICES),
        "location": fake.city()
    }

def generate_chunk(chunk_id):
    print(f"Generating chunk {chunk_id} ...")
    data = [generate_record() for _ in range(RECORDS_PER_CHUNK)]
    df = pd.DataFrame(data)
    file_path = os.path.join(OUTPUT_DIR, f"listening_data_{chunk_id:02d}.csv")
    df.to_csv(file_path, index=False)
    print(f"Saved chunk {chunk_id} to {file_path}")

if __name__ == "__main__":
    print(f"Generating {NUM_CHUNKS} CSV files in '{OUTPUT_DIR}' using {cpu_count()} CPUs...")
    with Pool(cpu_count()) as pool:
        pool.map(generate_chunk, range(NUM_CHUNKS))
    print("✅ Data generation complete.")
