# API Health Monitor

A self-hosted API monitoring system built with FastAPI and deployed via Terraform.

## Features
*   Monitor API endpoints (HTTP status check).
*   Track latency and uptime.
*   Simple REST API.
*   Architecture designed for AWS.

## Quickstart (Local)

1.  **Install Dependencies**:
    ```bash
    cd app
    pip install -r requirements.txt
    ```
2.  **Run Application**:
    ```bash
    python -m uvicorn app:app --reload
    ```
3.  **API Docs**: Open `http://localhost:8000/docs` to test endpoints.

## Deployment (AWS with Terraform)

1.  **Prerequisites**:
    *   AWS CLI configured.
    *   Terraform installed.

2.  **Provision Infrastructure**:
    ```bash
    cd terraform
    terraform init
    terraform apply
    ```
    *   Confirm the creation of resources (VPC, EC2, SG).
    *   Note the `public_ip` output.

3.  **Authentication (Alternative)**:
    If AWS CLI is not available, set environment variables before running Terraform:
    
    *PowerShell*:
    ```powershell
    $env:AWS_ACCESS_KEY_ID="your_access_key"
    $env:AWS_SECRET_ACCESS_KEY="your_secret_key"
    $env:AWS_DEFAULT_REGION="us-east-1"
    ```

4.  **Deploy Code**:
    *   Copy the `app` directory to the server (e.g., via `scp`).
    *   SSH into the server: `ssh -i <your-key.pem> ubuntu@<public_ip>`.
    *   Build and run the Docker container:
        ```bash
        cd app
        sudo docker build -t api-monitor .
        sudo docker run -d -p 80:80 api-monitor
        ```

## Architecture
See [docs/DESIGN.md](docs/DESIGN.md) for detailed architecture and trade-offs.
