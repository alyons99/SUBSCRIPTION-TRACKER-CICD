| Control | Family | Implementation |
|---------|--------|----------------|
| AC-6  | Least Privilege              | Container runs as non-root `appuser`; workflow token is `contents: read`, `id-token: write` granted only to the deploy job |
| IA-5  | Authenticator Management     | GitHub OIDC federation to an IAM role, short-lived credentials only, no stored AWS access keys |
| CM-2  | Baseline Configuration       | Dockerfile, pinned dependencies, and ECS task definition kept in version control |
| CM-3  | Configuration Change Control | Every change goes through the pipeline; deploy only from `main` behind the `production` environment |
| CM-7  | Least Functionality          | Slim base image, `.dockerignore` keeps tests and docs out of the image, single exposed port |
| RA-5  | Vulnerability Monitoring     | `pip-audit` scans dependencies for known CVEs on every run |
| SA-11 | Developer Testing            | pytest unit tests plus Ruff lint with Bandit security rules gate every build |
| SI-2  | Flaw Remediation             | A failed lint, test, or CVE scan blocks the build and deploy stages |
| SI-10 | Input Validation             | API rejects malformed input with 400s; all SQL uses parameterized queries |
| AU-12 | Audit Record Generation      | Container logs ship to CloudWatch via the `awslogs` driver (live deploy); pipeline run history in GitHub Actions |
