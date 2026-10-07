import json
import sys
from pathlib import Path
root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / "backend"))
from app.models import MatchEvent
schema = MatchEvent.model_json_schema()
schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
(root / "schemas").mkdir(exist_ok=True)
(root / "schemas/match-event.schema.json").write_text(json.dumps(schema, indent=2) + "\n", encoding="utf-8")
