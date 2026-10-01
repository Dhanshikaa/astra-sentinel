import json
from pathlib import Path
from database import upsert_article

DATA_PATH = Path(__file__).parent.parent / "data" / "articles.jsonl"

def load_starter_data():
    count = 0
    with open(DATA_PATH, encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                a = json.loads(line)
                if not a.get("title") or not a.get("content"):
                    continue
                upsert_article({**a, "category":"", "summary":"", "keywords":"", "topics":"", "entities":""})
                count += 1
            except json.JSONDecodeError:
                continue
    return count
