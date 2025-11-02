# API Load Testing (Locust)

This directory contains the scripts for load testing the backend API using [Locust](https://locust.io/).

The `locustfile.py` script simulates a population of virtual users that swarm the API endpoints to measure performance under stress.

## How to Run a Test

Follow these steps to start a new load test against the deployed AWS backend.

### 1. Configure the Target Host

Before running, you **must** tell Locust which server to attack.

* Open the `locustfile.py` script.
* Find the `host` variable (around line 24) and change it from the placeholder to your EC2 instance's public IP address and port.

    **Change this:**
    ```python
    host = "http://YOUR_EC2_PUBLIC_IPV4_ADDRESS:8080"
    ```
    **To this (example):**
    ```python
    host = "[http://3.14.22.101:8080](http://3.14.22.101:8080)"
    ```

### 2. Start the Locust Service

1.  Open your terminal and navigate to this directory:
    ```bash
    cd locust_test
    ```

2.  Run the `locust` command:
    ```bash
    locust
    ```

3.  Locust will start its web interface. You will see this in your terminal:
    ```
    [2025-11-02 15:30:00] ... Starting web interface at http://localhost:8089
    ```

### 3. Start the Test ("Swarm")

1.  Open your web browser and go to [http://localhost:8089](http://localhost:8089).

2.  You will see the Locust start screen. Fill in the test parameters:
    * **Number of users:** Total concurrent users to simulate, we use 30 in our test.
    * **Spawn rate:** How many new users to add per second, we use 10 in our test.

    
3.  Click **"Start swarming"**.

### 4. Monitor the Results

Click on the **"Statistics"** tab in the Locust UI to see the live performance metrics.


The key metrics for this project are:
* **Reqs/s (RPS):** Total requests per second. This is your system's throughput.
* **Failures (%):** The percentage of requests that failed (e.g., 5xx errors).
* **95%ile (ms):** The 95th percentile response time. This is your `p95 latency`, a key indicator of user experience under load.

## Simulated User Behavior

The `locustfile.py` script simulates the following user actions with different weights:

* **`GET /orders` (High Frequency):** Browsing all orders.
* **`GET /orders/[id]` (Medium Frequency):** Checking the status of a specific order.
* **`POST /orders` (Medium Frequency):** Placing a new order.
* **`PATCH /orders/[id]/status` (Low Frequency):** Simulating a worker processing an order.
* **`DELETE /orders/[id]` (Low Frequency):** Deleting an order.