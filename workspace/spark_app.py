from pyspark.sql import SparkSession
from pyspark.sql.functions import col, sum as _sum, countDistinct
import time

spark = (
    SparkSession.builder.appName("DemoJobs")
    .getOrCreate()
)
spark.sparkContext.setLogLevel("WARN")   # keep logs readable

# 1 ► Load raw CSV (creates Job 1 / Stage 1)
df = (
    spark.read.option("header", True)
    .option("inferSchema", True)
    .csv("/workspace/data/*.csv.gz")
    .repartition(8)  # makes eight partitions independent of #input files
    .cache()
)

print(f"Input rows: {df.count():,}")       # triggers Action 1 (Stage 2)
print(f"Partitions: {df.rdd.getNumPartitions()}")

# 2 ► Simple aggregation (Job 2 / Stage 3 → Stage 4)
country_agg = (
    df.groupBy("country")
      .agg(
          _sum("amount").alias("total_sales"),
          countDistinct("customer_id").alias("unique_customers")
      )
      .orderBy(col("total_sales").desc())
)

country_agg.show(10, truncate=False)

# 3 ► Self-join to generate extra shuffles (Job 3 / Stages 5–6)
# 3 ► Self-join to generate extra shuffles (Job 3 / Stages 5–6)
high_val = df.filter(col("amount") > 250)
joined = (
    high_val.alias("h")
    .join(df.alias("d"), ["customer_id"], "inner")
    .select(
        col("h.tx_id").alias("high_value_tx_id"),
        col("d.tx_id").alias("all_tx_id"),
        col("h.country"),
        col("h.amount").alias("high_value_amount"), # Rename for clarity
        col("d.amount").alias("all_tx_amount")      # Rename to avoid conflict
    )
)

print("Joined sample:")
joined.limit(5).show()

# 4 ► Write result Parquet (Job 4)
out_path = "/workspace/output/high_value_join"
joined.write.mode("overwrite").parquet(out_path)

print("▶ Sleeping 30s so you can inspect Spark UI at http://localhost:4040")
time.sleep(30)

print(f"✔ All done – data written to {out_path}")
spark.stop()