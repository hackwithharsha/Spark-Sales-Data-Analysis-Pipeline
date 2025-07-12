from pyspark.sql import SparkSession
from pyspark.sql.functions import col, hour, count, avg

spark = SparkSession.builder.appName("SpotifyAnalytics").getOrCreate()

df = spark.read.csv("/workspace/spotify_data/*.csv", header=True, inferSchema=True)

# Top 10 songs
df.groupBy("song_id") \
  .agg(count("*").alias("play_count")) \
  .orderBy(col("play_count").desc()) \
  .show(10)

# Average duration per user
df.groupBy("user_id") \
  .agg(avg("duration_ms").alias("avg_duration")) \
  .orderBy("avg_duration", ascending=False) \
  .show(10)

# Peak listening hours
df.withColumn("hour", hour("timestamp")) \
  .groupBy("hour") \
  .count() \
  .orderBy("count", ascending=False) \
  .show()
