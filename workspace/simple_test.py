from pyspark.sql import SparkSession

print("--- Starting Minimal Spark Test ---")

spark = (
    SparkSession.builder.appName("SimpleTest")
    .getOrCreate()
)

# Create an RDD from a simple list, no file access
data = [1, 2, 3, 4, 5]
rdd = spark.sparkContext.parallelize(data)
total = rdd.sum()

print("=" * 40)
print(f"      JOB SUCCEEDED! The sum is: {total}")
print("=" * 40)

spark.stop()