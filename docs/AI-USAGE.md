# AI assistance disclosure

OpenAI Codex (ChatGPT Work) generated the Milestone 2–4 implementation: FastAPI layers and schemas, SQLAlchemy/Alembic, Redis integration, triage providers and resilience, React UI and generated client integration, tests, GitHub Actions, Kubernetes manifests, scripts, and documentation. It inspected the existing Milestone 1 repository and supplied assignment PDF.

The implementation was revised during local verification: deferred/renamed type annotations prevented method names shadowing builtins; Redis pipeline typing was corrected; an OpenAPI-fetch error path was corrected to preserve server 409 details; proxy trust handling was made explicit; stats invalidation uses generation keys to handle concurrent cache fills; and migrations moved to one Kubernetes Job. Image references were reviewed for immutable pinning.

Actual verification and environment limitations are recorded in VALIDATION.md. AI did not produce peer reviews, branch-protection screenshots, historical commits, a fake failing PR, measured HPA/VPA results, or a demo video. Students must add their own learning/review notes here after reading and running the code, identifying what they changed and why. Be ready to explain any line at viva.
