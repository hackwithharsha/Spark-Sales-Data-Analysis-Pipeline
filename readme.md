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