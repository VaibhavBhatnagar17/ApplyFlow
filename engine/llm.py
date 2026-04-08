"""Open-source LLM helpers (Ollama-compatible) for insights and query expansion."""

from __future__ import annotations

import json
import requests


class OpenSourceInsights:
    def __init__(self, model: str = "llama3.1:8b", base_url: str = "http://localhost:11434"):
        self.model = model
        self.base_url = base_url.rstrip("/")

    def is_available(self) -> bool:
        try:
            r = requests.get(f"{self.base_url}/api/tags", timeout=2)
            return r.status_code == 200
        except Exception:
            return False

    def generate(self, prompt: str, system: str = "", temperature: float = 0.2) -> str:
        payload = {
            "model": self.model,
            "prompt": prompt,
            "system": system,
            "stream": False,
            "options": {"temperature": temperature},
        }
        try:
            r = requests.post(f"{self.base_url}/api/generate", json=payload, timeout=30)
            if r.status_code != 200:
                return ""
            data = r.json()
            return (data.get("response") or "").strip()
        except Exception:
            return ""

    def suggest_role_queries(self, profile, prefs, seed_role: str, location: str) -> list[str]:
        fallback = [
            seed_role,
            f"Senior {seed_role}",
            f"{seed_role} {location}",
            f"{seed_role} remote",
            f"{seed_role} {profile.years_experience}+ years",
        ]
        if not self.is_available():
            return fallback

        prompt = (
            "Generate 8 diverse job search query strings for this candidate. "
            "Return ONLY JSON array of strings.\n"
            f"Candidate title: {profile.current_title}\n"
            f"Experience: {profile.years_experience}\n"
            f"Core skills: {', '.join(profile.core_skills[:12])}\n"
            f"Target roles: {', '.join(prefs.target_titles[:10])}\n"
            f"Seed role: {seed_role}\n"
            f"Location: {location}"
        )
        text = self.generate(prompt, system="You are a job search strategist.")
        if not text:
            return fallback
        try:
            start = text.find("[")
            end = text.rfind("]")
            if start == -1 or end == -1:
                return fallback
            arr = json.loads(text[start : end + 1])
            cleaned = [str(x).strip() for x in arr if str(x).strip()]
            return cleaned[:8] if cleaned else fallback
        except Exception:
            return fallback

    def dashboard_insights(self, profile, prefs, results) -> str:
        top = results[:12]
        if not top:
            return "No job results yet. Run a search first."

        top_companies = {}
        top_titles = {}
        for r in top:
            top_companies[r.job.company] = top_companies.get(r.job.company, 0) + 1
            top_titles[r.job.title] = top_titles.get(r.job.title, 0) + 1

        deterministic = (
            "### Insight Summary\n"
            f"- Your current profile is strongest for: **{profile.current_title or 'your selected roles'}**\n"
            f"- Top matching companies in current pool: **{', '.join(list(top_companies.keys())[:5])}**\n"
            f"- Most frequent role patterns: **{', '.join(list(top_titles.keys())[:4])}**\n"
            "- Recommendation: prioritize excellent matches first, then good matches in preferred companies.\n"
        )

        if not self.is_available():
            return deterministic + "\n_Open-source LLM is not running locally. Showing deterministic insights._"

        prompt = (
            "Analyze this job-match snapshot and provide concise actionable insights. "
            "Use markdown bullets with: strengths, gaps, search refinement, next 5 actions.\n"
            f"Profile title: {profile.current_title}\n"
            f"Experience: {profile.years_experience}\n"
            f"Core skills: {', '.join(profile.core_skills[:15])}\n"
            f"Target roles: {', '.join(prefs.target_titles[:10])}\n"
            f"Top jobs: "
            + "; ".join([f"{r.job.company}:{r.job.title}:{int(r.score*100)}%" for r in top])
        )
        text = self.generate(prompt, system="You are a senior career strategist.")
        if not text:
            return deterministic
        return text

    def search_run_insights(self, role: str, location: str, ranked_results) -> str:
        if not ranked_results:
            return "No live jobs found in this run."

        deterministic = (
            f"Found **{len(ranked_results)}** jobs for **{role}** in **{location}**. "
            f"Top score: **{int(ranked_results[0].score*100)}%**."
        )

        if not self.is_available():
            return deterministic + " _(LLM offline; deterministic summary shown.)_"

        prompt = (
            "Summarize this live job-search run in 5 bullets: market signal, role alignment, risk flags, "
            "best-next-search-query, and apply strategy.\n"
            f"Role: {role}, Location: {location}\n"
            + "; ".join([f"{r.job.company}|{r.job.title}|{int(r.score*100)}%" for r in ranked_results[:10]])
        )
        text = self.generate(prompt, system="You are an AI job search copilot.")
        return text or deterministic
