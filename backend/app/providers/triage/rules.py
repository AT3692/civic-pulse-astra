import re

from app.schemas import Category, Priority, TriageResult


class RuleBasedTriage:
    name = "rules"

    async def triage(self, text: str, location: str) -> TriageResult:
        body = text.casefold()
        terms = {
            Category.water: ("water", "pipe", "flood", "pani", "burst main"),
            Category.streetlights: ("streetlight", "street light", "lamp post"),
            Category.electricity: ("electric", "power", "wire", "transformer", "bijli"),
            Category.sanitation: ("garbage", "sewage", "sewer", "rubbish", "kachra", "drain"),
            Category.roads: ("pothole", "road", "pavement", "footpath"),
        }
        category = next((cat for cat, words in terms.items() if any(word in body for word in words)), Category.other)
        high = any(
            word in body
            for word in ("flood", "burst", "sparking", "exposed wire", "fire", "danger", "injur", "entering homes")
        )
        low = any(word in body for word in ("faded", "cosmetic", "paint"))
        return TriageResult(
            category=category,
            priority=Priority.high if high else Priority.low if low else Priority.normal,
            summary=re.sub(r"\s+", " ", text).strip()[:140],
            confidence=0.55,
        )
