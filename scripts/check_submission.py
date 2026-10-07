"""Mechanical checks only. Does not manufacture collaboration or deployment evidence."""

import ast
import re
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
errors = []
tracked = subprocess.check_output(["git", "ls-files", "-z"], cwd=ROOT, text=True).split(
    "\0"
)
for name in tracked:
    filename = Path(name).name
    if (
        filename == ".env" or filename.startswith(".env.")
    ) and filename != ".env.example":
        errors.append(f"Tracked environment file: {name}; remove it from the index")
required = [
    "backend/alembic/versions/0001_complaints.py",
    "backend/openapi.json",
    "frontend/package-lock.json",
    "frontend/src/api/schema.d.ts",
    ".github/workflows/ci.yml",
    ".github/workflows/cd.yml",
    ".github/workflows/release.yml",
    "k8s/overlays/dev/kustomization.yaml",
    "k8s/overlays/prod/kustomization.yaml",
    "docs/RUNBOOK.md",
    "docs/ENGINEERING-NOTES.md",
    "docs/AI-USAGE.md",
    "docs/TRIAGE.md",
    "load/k6-script.js",
]
for file in required:
    if not (ROOT / file).is_file():
        errors.append(f"Missing {file}")
for file in ["compose.yaml", "compose.prod.yaml"]:
    config = yaml.safe_load((ROOT / file).read_text())
    services = config["services"]
    if services["frontend"]["networks"] != ["edge"]:
        errors.append(f"{file}: frontend must join edge only")
    for name in ["postgres", "redis"]:
        if services[name]["networks"] != ["internal"]:
            errors.append(f"{file}: {name} must join internal only")
        if file == "compose.prod.yaml" and services[name].get("ports"):
            errors.append(f"{file}: data service ports exposed")
    if not config["networks"]["internal"].get("internal"):
        errors.append(f"{file}: internal isolation missing")
    if file.endswith("prod.yaml") and any("build" in svc for svc in services.values()):
        errors.append("Production Compose must not build images")
for file in (ROOT / "backend/app/routes").glob("*.py"):
    tree = ast.parse(file.read_text())
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.ImportFrom)
            and node.module
            and ("sqlalchemy" in node.module or "repositories" in node.module)
        ):
            errors.append(
                f"{file.relative_to(ROOT)}: routes must not access persistence"
            )
for file in (ROOT / "k8s/base").glob("*.yaml"):
    for obj in yaml.safe_load_all(file.read_text()):
        if not obj:
            continue
        if obj["kind"] == "Deployment" and obj["metadata"]["name"] == "postgres":
            errors.append("Postgres must be a StatefulSet")
        if obj["kind"] == "Service" and obj["spec"].get("type") != "ClusterIP":
            errors.append("Application services must use ClusterIP")
        pod = obj.get("spec", {}).get("template", {}).get("spec", {})
        for container in pod.get("containers", []) + pod.get("initContainers", []):
            if not {"requests", "limits"} <= container.get("resources", {}).keys():
                errors.append(f"{file.name}: resources missing")
            if container["image"].endswith(":latest"):
                errors.append(f"{file.name}: latest must not be deployed")
for file in (ROOT / ".github/workflows").glob("*.yml"):
    workflow = yaml.safe_load(file.read_text())
    if "permissions" not in workflow:
        errors.append(f"{file.name}: explicit permissions missing")
    for name, job in workflow["jobs"].items():
        if name in ["build-push", "deploy-k8s", "publish"] and "needs" not in job:
            errors.append(f"{file.name}/{name}: publishing/deploying needs a gate")
        for step in job.get("steps", []):
            action = step.get("uses", "")
            if action and not re.search(r"@(?:v?\d|[0-9a-f]{40})", action):
                errors.append(f"{file.name}: action is not version-pinned: {action}")
if errors:
    print("\n".join("FAIL: " + error for error in errors))
    sys.exit(1)
print(
    "PASS: repository structure, layer boundary, network isolation, deployment resources, workflow gates"
)
print(
    "Manual evidence still required: peer reviews, branch protection, live CI/CD, load tests, video."
)
