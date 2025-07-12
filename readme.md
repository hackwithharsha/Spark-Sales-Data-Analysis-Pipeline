# Spark Sales Data Analysis Pipeline

This project provides a complete, dockerized environment to run a typical sales data processing pipeline using PySpark. The application reads raw transaction data, performs aggregations to calculate total sales by country, identifies high-value transactions, and joins them back to the original dataset to find related customer activity.

The final processed data is saved in the efficient Parquet format. The entire Spark cluster (master, workers, and history server) is managed by Docker Compose for easy setup and teardown.

## Features

  * **Realistic Data Pipeline:** Analyzes and aggregates sales data from raw CSV files.
  * **Complex Transformations:** Demonstrates key Spark operations like `groupBy`, `join`, and `cache`.
  * **Live UI Inspection:** Includes a 30-second pause to allow inspection of the live Spark Driver UI on port `4040`.
  * **Dockerized Spark Cluster:** Easily launch a Spark 3.4 cluster with one command.
  * **Persistent History:** Includes a Spark History Server to analyze the UI of completed applications.
  * **Robust Data Storage:** Uses a Docker-managed named volume to avoid common host-machine permission issues.

## Prerequisites

Before you begin, ensure you have the following installed:

  * [Docker](https://docs.docker.com/get-docker/)
  * [Docker Compose](https://docs.docker.com/compose/install/)

## Project Structure

To run this project, your files and folders must be organized as follows on your local machine:

```
.
├── docker-compose.yml
├── README.md
└── workspace/
    ├── spark_app.py
    └── data/
        └── transactions/
            └── (Your .csv.gz files go here)
```

## Getting Started

Follow these steps to set up the environment and run the Spark application.

### Step 1:  Generate Sample Data

```bash
>>> python3 generate_data.py
```

### Step 2: Launch the Spark Cluster

This command will start the Spark master, workers, and the History Server.

```bash
docker-compose up -d
```

### Step 3: Run the Spark Application

Execute the PySpark script using `docker exec` to run `spark-submit` inside the master container.

```bash
docker exec -it spark-master \
  spark-submit \
    --master spark://spark-master:7077 \
    --conf spark.jars.ivy=/home/spark/.ivy2 \
    /workspace/simple_test.py
```

```bash
docker exec -it spark-master \
  spark-submit \
    --master spark://spark-master:7077 \
    --deploy-mode client \
    --driver-memory 2G \
    --executor-memory 2G \
    --executor-cores 2 \
    --conf spark.sql.shuffle.partitions=8 \
    --conf spark.jars.ivy=/home/spark/.ivy2 \
    --conf spark.eventLog.enabled=true \
    --conf spark.eventLog.dir=/workspace/spark-events \
    --conf "spark.hadoop.hadoop.security.authentication=simple" \
    --conf "spark.driver.extraJavaOptions=-DHADOOP_USER_NAME=spark" \
    --conf "spark.executor.extraJavaOptions=-DHADOOP_USER_NAME=spark" \
    /workspace/spark_app.py
```

The script will now run. **It will pause for 30 seconds before the final step**, giving you a window to check the live UI. The final Parquet files will be written to the `/workspace/output/` directory inside the Docker volume.

## Exploring the Spark UI

You can monitor and analyze your Spark jobs using three different web interfaces:

  * **Spark Master UI (`http://localhost:8080`)**

      * Shows the overall health of your cluster, including connected workers.

  * **Live Application UI (`http://localhost:4040`)**

      * This is the detailed UI for your *currently running* job, served directly by the Spark driver.
      * **It is only available during the 30-second pause in the script.**

  * **Spark History Server (`http://localhost:18080`)**

      * Use this to view the full, detailed UI for applications that have **finished**.

## Cleanup

To stop and completely remove all containers and the named volume, run the following command:

```bash
docker-compose down --volumes
```

## Spark Concepts

### Why So Many Jobs? Actions vs. Physical Execution

While our `spark app` has 4 clear logical actions, the Spark UI shows 13 jobs. This is normal and happens because Spark often breaks down a single user action into multiple smaller, physical jobs behind the scenes.

The key concept is that **one *action* in our code does not always equal one *job* in the UI.** Spark's Catalyst optimizer creates a physical execution plan, and many operations, especially involving schema inference, DataFrame previews (`show`), and writing files, are composed of multiple smaller jobs.

Many of these extra jobs are very fast "housekeeping" tasks. **Your goal for optimization is to find the few jobs with a high "Duration."**

### Decoding the Jobs in Your Application

Let's map your Python code to the jobs you're seeing in the History Server. The Job IDs (0-12) correspond to the order of execution.

#### The "Hidden" Jobs (Jobs 0-3 approx.)

These jobs are triggered by Spark's internal mechanisms before your first main action.

* **`option("inferSchema", True)`:** This is the biggest source of "hidden" jobs. To figure out the data types of your columns, Spark **must read a portion of your CSV files.** This requires one or more initial jobs before your code even gets to the `.count()` action. The descriptions for these jobs in the UI are often cryptic, relating to internal calls like `first()` or `collect()`.

#### Your Main Action #1: `df.count()` (Job 4 approx.)

* **Your Code:** `print(f"Input rows: {df.count():,}")`
* **The Job:** This directly corresponds to the job in the UI with the description `count at spark_app.py:33`. This is the first major action you explicitly called. It reads the entire dataset (and caches it in memory because you used `.cache()`) to get the total row count.

#### Your Main Action #2: `country_agg.show(10)` (Jobs 5-7 approx.)

* **Your Code:** `country_agg.show(10, truncate=False)`
* **The Jobs:** The `.show()` command is more complex than it looks. It might trigger multiple jobs to:
    1.  Execute the `groupBy` and `agg` operations.
    2.  Perform the `orderBy` to sort the results.
    3.  `take` the top 10 results and bring them back to the driver to be printed.
    Each of these steps can be registered as a separate job in the UI.

#### Your Main Action #3: `joined.limit(5).show()` (Jobs 8-10 approx.)

* **Your Code:** `joined.limit(5).show()`
* **The Jobs:** This is similar to the previous `.show()` action. It triggers jobs to execute the `filter` and the expensive `join` operation, then takes the first 5 results to show you.

#### Your Main Action #4: `joined.write.parquet()` (Jobs 11-12 approx.)

* **Your Code:** `joined.write.mode("overwrite").parquet(out_path)`
* **The Jobs:** Writing data is also a multi-step process. Spark might launch separate jobs to:
    1.  Calculate the final `joined` DataFrame.
    2.  Write the actual data files (one per partition) into the output directory.
    3.  Write a `_SUCCESS` marker file to indicate the job is complete.

### How to Use This for Optimization

Now for the most important part: how to use this information.

1.  **Ignore the Fast Jobs:** Don't worry about the jobs that take milliseconds. These are Spark's internal housekeeping. They are not your bottleneck.

2.  **Find the Slowest Job:** In the "Completed Jobs" table, look at the **Duration** column. Identify the job (or jobs) that take the longest. **This is where 99% of your optimization effort should go.** For example, if the job for the `join` or the `write.parquet` operation is taking minutes, that's your target.

3.  **Analyze the Stages:** Click on the **Description** of your slowest job. This will take you to the "Stages" view for that job. Here, look for:
    * **Shuffle Read / Write:** Large amounts of shuffle data indicate an expensive, wide transformation (like `groupBy`, `join`, `orderBy`). This is a common source of performance issues.
    * **Task Skew:** Look at the table of tasks at the bottom of the stage page. If one or two tasks take much, much longer than the others (the "Max" duration is far from the "Median"), you have **data skew**. This means one of your partitions is overloaded. You can often fix this by `repartition()`ing your data on a different key.

## Spotify Data Example

```bash
# To generate fake Spotify data
>>> python3 spotify_data.py
```

````bash
docker exec -it spark-master \
  spark-submit \
    --master spark://spark-master:7077 \
    --deploy-mode client \
    --driver-memory 2G \
    --executor-memory 2G \
    --executor-cores 2 \
    --conf spark.sql.shuffle.partitions=8 \
    --conf spark.jars.ivy=/home/spark/.ivy2 \
    --conf spark.eventLog.enabled=true \
    --conf spark.eventLog.dir=/workspace/spark-events \
    --conf "spark.hadoop.hadoop.security.authentication=simple" \
    --conf "spark.driver.extraJavaOptions=-DHADOOP_USER_NAME=spark" \
    --conf "spark.executor.extraJavaOptions=-DHADOOP_USER_NAME=spark" \
    /workspace/spotify_app.py
```