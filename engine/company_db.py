"""Load and filter the company research database."""

import json
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"


def load_companies() -> list[dict]:
    path = DATA_DIR / "company_research.json"
    if not path.exists():
        return []
    with open(path) as f:
        data = json.load(f)
    return data.get("companies", [])


def filter_companies(
    companies: list[dict],
    tier: int | None = None,
    industry: str | None = None,
    location: str | None = None,
    search: str | None = None,
) -> list[dict]:
    results = companies
    if tier is not None:
        results = [c for c in results if c.get("tier") == tier]
    if industry:
        il = industry.lower()
        results = [c for c in results if il in c.get("industry", "").lower()]
    if location:
        ll = location.lower()
        results = [
            c for c in results
            if ll in str(c.get("india_offices", [])).lower()
            or ll in c.get("hq", "").lower()
        ]
    if search:
        sl = search.lower()
        results = [
            c for c in results
            if sl in c.get("name", "").lower()
            or sl in c.get("industry", "").lower()
            or sl in str(c.get("why_good_fit", [])).lower()
        ]
    return results


def get_industries(companies: list[dict]) -> list[str]:
    return sorted({c.get("industry", "Other") for c in companies if c.get("industry")})


def get_tier_label(tier: int) -> str:
    return {1: "Dream", 2: "Strong Fit", 3: "Good Match"}.get(tier, "Other")
