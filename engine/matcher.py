"""Job-profile matching engine using TF-IDF cosine similarity + multi-signal scoring."""

import re
from dataclasses import dataclass, field

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .profile import Profile, JobPreferences
from .job_model import JobListing


@dataclass
class MatchResult:
    job: JobListing
    score: float
    title_score: float = 0.0
    skill_score: float = 0.0
    keyword_score: float = 0.0
    company_score: float = 0.0
    location_score: float = 0.0
    reasons: list = field(default_factory=list)


class JobMatcher:
    WEIGHTS = {
        "title": 0.25,
        "skills": 0.30,
        "keywords": 0.20,
        "company": 0.10,
        "location": 0.15,
    }

    def __init__(self, profile: Profile, prefs: JobPreferences):
        self.profile = profile
        self.prefs = prefs
        self._profile_text = self._build_profile_text()
        self._vectorizer = TfidfVectorizer(
            max_features=3000, ngram_range=(1, 2),
            stop_words="english", min_df=1,
        )
        self._profile_skills_lower = {s.lower() for s in profile.core_skills}
        self._must_have_lower = {k.lower() for k in prefs.must_have_keywords}
        self._nice_to_have_lower = {k.lower() for k in prefs.nice_to_have_keywords}
        self._exclude_lower = {k.lower() for k in prefs.exclude_keywords}
        self._target_titles_lower = [t.lower() for t in prefs.target_titles]
        self._preferred_lower = {c.lower() for c in prefs.preferred_companies}
        self._excluded_lower = {c.lower() for c in prefs.excluded_companies}
        self._locations_lower = {loc.lower() for loc in prefs.target_locations}

    def _build_profile_text(self) -> str:
        return " ".join([
            self.profile.summary,
            self.profile.current_title,
            " ".join(self.profile.core_skills),
            " ".join(self.profile.key_achievements),
        ])

    def score_jobs(self, jobs: list[JobListing]) -> list[MatchResult]:
        results = []
        for job in jobs:
            r = self._score_one(job)
            if r:
                results.append(r)
        results.sort(key=lambda r: r.score, reverse=True)
        for r in results:
            r.job.match_score = r.score
        return results

    def _score_one(self, job: JobListing) -> MatchResult | None:
        if job.company.lower() in self._excluded_lower:
            return None

        text_lower = f"{job.title} {job.description} {job.company}".lower()
        for exc in self._exclude_lower:
            if exc in text_lower:
                return None

        reasons = []
        title_s = self._score_title(job.title, reasons)
        skill_s = self._score_skills(job, reasons)
        kw_s = self._score_keywords(job, reasons)
        co_s = self._score_company(job.company, reasons)
        loc_s = self._score_location(job.location, reasons)

        composite = (
            self.WEIGHTS["title"] * title_s
            + self.WEIGHTS["skills"] * skill_s
            + self.WEIGHTS["keywords"] * kw_s
            + self.WEIGHTS["company"] * co_s
            + self.WEIGHTS["location"] * loc_s
        )
        if job.easy_apply:
            composite = min(1.0, composite + 0.05)
            reasons.append("Easy Apply available")

        return MatchResult(
            job=job, score=round(composite, 3),
            title_score=round(title_s, 3), skill_score=round(skill_s, 3),
            keyword_score=round(kw_s, 3), company_score=round(co_s, 3),
            location_score=round(loc_s, 3), reasons=reasons,
        )

    def _score_title(self, title: str, reasons: list) -> float:
        tl = title.lower()
        for target in self._target_titles_lower:
            if target in tl or tl in target:
                reasons.append(f"Strong title match: '{title}'")
                return 1.0
        words = set(re.findall(r"\w+", tl))
        best = 0.0
        for target in self._target_titles_lower:
            tw = set(re.findall(r"\w+", target))
            if tw:
                best = max(best, len(words & tw) / len(tw))
        return best

    def _score_skills(self, job: JobListing, reasons: list) -> float:
        job_text = f"{job.title} {job.description}"
        if len(job_text.strip()) < 20:
            return self._skill_keyword_fallback(job)
        try:
            tfidf = self._vectorizer.fit_transform([self._profile_text, job_text])
            sim = float(cosine_similarity(tfidf[0:1], tfidf[1:2])[0][0])
            score = min(sim * 2, 1.0)
            if score > 0.3:
                reasons.append(f"Good skill overlap ({score:.0%})")
            return score
        except Exception:
            return self._skill_keyword_fallback(job)

    def _skill_keyword_fallback(self, job: JobListing) -> float:
        text = f"{job.title} {job.description}".lower()
        hits = sum(1 for s in self._profile_skills_lower if s in text)
        return min(hits / max(len(self._profile_skills_lower) * 0.3, 1), 1.0)

    def _score_keywords(self, job: JobListing, reasons: list) -> float:
        text = f"{job.title} {job.description}".lower()
        must_hits = sum(1 for k in self._must_have_lower if k in text)
        nice_hits = sum(1 for k in self._nice_to_have_lower if k in text)
        must_total = len(self._must_have_lower) or 1
        nice_total = len(self._nice_to_have_lower) or 1
        if must_hits:
            reasons.append(f"Must-have keywords: {must_hits}/{must_total}")
        if nice_hits:
            reasons.append(f"Nice-to-have: {nice_hits}/{nice_total}")
        return 0.7 * (must_hits / must_total) + 0.3 * (nice_hits / nice_total)

    def _score_company(self, company: str, reasons: list) -> float:
        cl = company.lower()
        if cl in self._preferred_lower:
            reasons.append(f"Preferred company: {company}")
            return 1.0
        for p in self._preferred_lower:
            if p in cl or cl in p:
                reasons.append(f"Preferred company: {company}")
                return 0.8
        return 0.3

    def _score_location(self, location: str, reasons: list) -> float:
        ll = location.lower()
        if "remote" in ll:
            return 1.0
        for t in self._locations_lower:
            if t in ll or ll in t:
                return 1.0
        if self.profile.willing_to_relocate:
            return 0.4
        return 0.1
