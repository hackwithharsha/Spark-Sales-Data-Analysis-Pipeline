"""
Write N fake transactions into /workspace/data/transactions.csv.gz
Usage:  python generate_data.py --rows 1000000
"""
from faker import Faker
from random import uniform
from pathlib import Path
import argparse, csv, gzip

fake = Faker()
argp = argparse.ArgumentParser()
argp.add_argument("--rows", type=int, default=1_000_000)
rows = argp.parse_args().rows

out_dir = Path("./workspace/data")
out_dir.mkdir(parents=True, exist_ok=True)
outfile = out_dir / "transactions.csv.gz"

with gzip.open(outfile, "wt", newline="") as f:
    w = csv.writer(f)
    w.writerow(["tx_id", "customer_id", "country", "amount", "timestamp"])
    for i in range(rows):
        w.writerow([
            i,
            fake.uuid4(),
            fake.country_code(),
            round(uniform(5.0, 500.0), 2),
            fake.date_time_this_decade().isoformat(),
        ])

print(f"✔ Generated {rows:,} rows → {outfile}")