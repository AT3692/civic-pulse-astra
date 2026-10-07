# ADR 0003 — Immutable deployments and explicit schema jobs

Status: accepted.

GHCR images carry full commit SHA tags and CD outputs content digests. Kubernetes receives digests; rollback can identify exactly what ran. Latest is an alias for humans, never a deployment input. BuildKit attestations, Syft SBOMs, Trivy scans, and Cosign signing/verification accompany published artifacts. Third-party Actions are version-tag pinned; a further supply-chain improvement is reviewing and pinning every Action to a commit SHA.

A single Job applies Alembic migrations. Each backend pod waits for the expected version without performing DDL. This avoids two replicas racing migrations. The deployment script preserves externally provisioned Secrets instead of overwriting them with committed placeholders. Updating the schema requires updating the init-container version gate too.

`rollout undo` is the incident response; reapplying a recorded prior digest pair is the auditable repair. Neither reverses a destructive database migration. Use expand/contract migrations and a tested backup before destructive changes. CI clusters are ephemeral; deploying to a persistent cluster is a separate operational decision.
