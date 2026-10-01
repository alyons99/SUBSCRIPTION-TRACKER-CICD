# Architecture

## Overview

This project is a containerized Flask REST API for tracking recurring 
subscriptions, shipped by a fully automated GitHub Actions pipeline. 
Every push runs lint, tests, and a dependency CVE scan, builds a Docker 
image, smoke-tests it, and on `main` deploys it to AWS ECS Fargate with 
zero manual steps. The pipeline is aligned with NIST 800-53 
configuration management and system integrity controls.

The same image that passes the smoke test is the one that gets 
deployed. It is never rebuilt between stages.

## Pipeline Stages

### Stage 1 Lint

Ruff checks style, import order, common bugs, and the Bandit (`S`) 
security rule set. Formatting is verified with `ruff format --check`. 
Runs in parallel with Stage 2.

### Stage 2 Test

- **pytest**  unit tests against a throwaway SQLite database per test
- **pip-audit**  checks `requirements.txt` against known CVE databases

Any failure in Stage 1 or Stage 2 stops the pipeline before a build.

### Stage 3 Build

Builds the Docker image tagged with the commit SHA, starts it, and 
polls `/health` until it responds. If the container doesn't come up 
healthy within 20 seconds the job fails and prints the container logs. 
The passing image is saved as a workflow artifact for the deploy stage.

### Stage 4 Deploy

Runs only on pushes to `main`, inside the `production` GitHub 
environment, with a concurrency lock so two deploys never overlap.

**Stub mode (default)**  
Prints each deployment step it would take. This lets the full pipeline 
run green without an AWS account.

**Live mode** `AWS_DEPLOY_ENABLED=true`  
1. Assumes an IAM role through GitHub OIDC (no stored access keys)
2. Pushes the image to Amazon ECR, tagged with the commit SHA
3. Renders `deploy/task-definition.json` with the new image URI
4. Updates the ECS Fargate service and waits for it to reach a stable, 
   healthy state

## Application

**Flask API**  
Served by gunicorn (2 workers) on port 8000 as a non-root user. A 
Docker `HEALTHCHECK` and an ECS health check both call `/health`.

| Method | Path | Purpose |
|--------|------|---------|
| GET    | `/health` | Liveness check |
| GET    | `/subscriptions` | List all, sorted by renewal date |
| POST   | `/subscriptions` | Create a subscription |
| GET    | `/subscriptions/<id>` | Get one |
| DELETE | `/subscriptions/<id>` | Delete one |
| GET    | `/subscriptions/summary` | Count plus monthly and yearly spend (yearly plans prorated) |

**Validation**  
`name` must be non-empty, `cost` a non-negative number, `billing_cycle` 
either `monthly` or `yearly`, and `renewal_date` an ISO `YYYY-MM-DD` 
date. Invalid input returns 400 with an error message.

**SQLite**  
Stored at `DATABASE_PATH` (default `/data/subscriptions.db`). The 
schema is created on startup.

---

## Production Considerations

This implementation is optimized for simplicity and demonstration. A 
production deployment would incorporate the following changes:

| Component | Demo Configuration | Production Configuration |
|-----------|-------------------|--------------------------|
| Database | SQLite in the container | RDS PostgreSQL or DynamoDB (Fargate storage is lost when a task is replaced) |
| Deploy | Stubbed until enabled | Live, with required reviewers on the `production` environment |
| Image scanning | Dependency scan only | ECR scan on push plus a container image scanner in CI |
| Image signing | None | Signed images verified before deploy |
| Auth | None | API keys or Cognito in front of an ALB |
| Transport | Plain HTTP on 8000 | ALB with an ACM certificate, HTTPS only |
| Scaling | Single task | ECS service auto scaling, multiple AZs |

---
