"""Replace image references without persisting secrets or modifying tracked overlays."""

import os
import sys
from pathlib import Path

import yaml

objects = list(yaml.safe_load_all(Path(sys.argv[1]).read_text()))
objects = [o for o in objects if o and o["kind"] != "Secret"]
for obj in objects:
    spec = obj.get("spec", {}).get("template", {}).get("spec", {})
    for container in spec.get("containers", []) + spec.get("initContainers", []):
        image = container.get("image", "")
        if "civicpulse-backend" in image:
            container["image"] = os.environ["BACKEND_IMAGE"]
        if "civicpulse-frontend" in image:
            container["image"] = os.environ["FRONTEND_IMAGE"]
    if obj["kind"] == "ConfigMap" and os.environ.get("DEPLOY_TRIAGE_PROVIDER"):
        obj["data"]["TRIAGE_PROVIDER"] = os.environ["DEPLOY_TRIAGE_PROVIDER"]
Path(sys.argv[2]).write_text(yaml.safe_dump_all(objects, sort_keys=False))
