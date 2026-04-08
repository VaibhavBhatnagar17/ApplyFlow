"""Standardized job listing model."""

import hashlib
from dataclasses import dataclass, field, asdict
from datetime import datetime


@dataclass
class JobListing:
    job_id: str
    title: str
    company: str
    location: str
    description: str
    url: str
    platform: str
    salary: str = ""
    job_type: str = ""
    remote: str = ""
    posted_date: str = ""
    easy_apply: bool = False
    scraped_at: str = field(default_factory=lambda: datetime.now().isoformat())
    match_score: float = 0.0
    applied: bool = False
    status: str = "new"
    experience: str = ""
    skills_matched: list = field(default_factory=list)
    match_quality: str = ""
    freshness: str = ""

    def to_dict(self):
        return asdict(self)

    @staticmethod
    def generate_id(url: str, title: str, company: str) -> str:
        raw = f"{url}|{title}|{company}"
        return hashlib.md5(raw.encode()).hexdigest()[:12]

    @classmethod
    def from_active_job(cls, entry: dict) -> "JobListing":
        """Create a JobListing from an active_jobs.json entry."""
        url = entry.get("url", "")
        title = entry.get("title", "")
        company = entry.get("company", "")
        skills = entry.get("skills_matched", [])
        exp = entry.get("experience", "")
        quality = entry.get("match_quality", "good")

        quality_scores = {"excellent": 0.9, "good": 0.7, "stretch": 0.5}
        desc = f"{title} at {company}. Skills: {', '.join(skills)}. Experience: {exp}"

        return cls(
            job_id=cls.generate_id(url, title, company),
            title=title,
            company=company,
            location=entry.get("location", ""),
            description=desc,
            url=url,
            platform=entry.get("platform", ""),
            posted_date=entry.get("posted", ""),
            match_score=quality_scores.get(quality, 0.7),
            status=entry.get("status", "new"),
            experience=exp,
            skills_matched=skills,
            match_quality=quality,
            freshness=entry.get("freshness", ""),
            easy_apply="linkedin" in entry.get("platform", "").lower()
                       or "easy" in entry.get("platform", "").lower(),
        )
