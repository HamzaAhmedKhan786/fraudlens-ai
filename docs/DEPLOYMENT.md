# Production deployment

This compose profile is a single-host production baseline, not a substitute for managed HA services.
Terminate TLS in a reverse proxy/load balancer and expose only HTTPS; API and web bind to loopback.

1. Copy `.env.production.example` to `.env.production` and replace every secret/hostname.
2. Back up PostgreSQL and object storage before upgrades.
3. Run `./scripts/deploy-production.ps1` from PowerShell as the deployment user.
4. The script builds immutable images, runs Alembic once, starts services, and verifies API/web health.
5. Roll back application images only after checking migration compatibility; never downgrade the DB blindly.

Production gates: external OIDC with MFA, durable PostgreSQL/Redis/Kafka/object storage, encrypted backups,
secret manager injection, TLS, monitoring/alerting, log redaction, vulnerability scans, restore drills, and
provider credentials. Stripe and GPU inference stay disabled until their separate security reviews complete.
