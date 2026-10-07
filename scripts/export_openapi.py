import json
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / "backend"))
from app.main import create_app

(root / "backend/openapi.json").write_text(
    json.dumps(create_app().openapi(), indent=2) + "\n"
)
