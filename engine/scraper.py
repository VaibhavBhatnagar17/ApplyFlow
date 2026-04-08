"""Lightweight real-time job scraper using requests + BeautifulSoup."""

import re
import time
import logging
from datetime import datetime, timedelta
from urllib.parse import urlencode

import requests
from bs4 import BeautifulSoup

from .job_model import JobListing

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


class JobScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)

    def search(
        self,
        title: str,
        location: str,
        platforms: list[str] | None = None,
        max_jobs: int = 50,
        posted_within_days: int = 14,
        min_experience: int = 0,
        max_experience: int = 40,
    ) -> list[JobListing]:
        if platforms is None:
            platforms = ["linkedin", "indeed", "naukri"]

        all_jobs: list[JobListing] = []

        for platform in platforms:
            try:
                if platform == "linkedin":
                    all_jobs.extend(self._search_linkedin(title, location, max_jobs=max_jobs))
                elif platform == "indeed":
                    all_jobs.extend(
                        self._search_indeed(
                            title,
                            location,
                            max_jobs=max_jobs,
                            posted_within_days=posted_within_days,
                        )
                    )
                elif platform == "naukri":
                    all_jobs.extend(
                        self._search_naukri(
                            title,
                            location,
                            max_jobs=max_jobs,
                            min_experience=min_experience,
                        )
                    )
                time.sleep(1.0)
            except Exception as e:
                logger.warning(f"{platform} search failed: {e}")

        unique = self._deduplicate(all_jobs)
        filtered = self._apply_filters(
            unique,
            posted_within_days=posted_within_days,
            min_experience=min_experience,
            max_experience=max_experience,
        )
        return filtered[:max_jobs]

    def _search_linkedin(self, title: str, location: str, max_jobs: int = 50) -> list[JobListing]:
        jobs: list[JobListing] = []
        starts = [0, 25, 50]

        for start in starts:
            params = {
                "keywords": title,
                "location": location,
                "f_TPR": "r2592000",  # 30 days
                "start": start,
            }
            url = f"https://www.linkedin.com/jobs/search/?{urlencode(params)}"

            try:
                resp = self.session.get(url, timeout=15)
                if resp.status_code != 200:
                    continue

                soup = BeautifulSoup(resp.text, "html.parser")
                cards = soup.find_all("div", class_=re.compile(r"base-card|job-search-card"))

                for card in cards:
                    try:
                        title_el = card.find("h3", class_=re.compile(r"base-search-card__title"))
                        company_el = card.find("h4", class_=re.compile(r"base-search-card__subtitle"))
                        link_el = card.find("a", class_=re.compile(r"base-card__full-link"))
                        loc_el = card.find("span", class_=re.compile(r"job-search-card__location"))
                        date_el = card.find("time")

                        if not all([title_el, company_el, link_el]):
                            continue

                        jt = title_el.get_text(strip=True)
                        co = company_el.get_text(strip=True)
                        ju = link_el.get("href", "").split("?")[0]
                        jl = loc_el.get_text(strip=True) if loc_el else location
                        posted = date_el.get("datetime", "") if date_el else ""
                        full_text = card.get_text(" ", strip=True)
                        exp = self._extract_experience(full_text)

                        jobs.append(
                            JobListing(
                                job_id=JobListing.generate_id(ju, jt, co),
                                title=jt,
                                company=co,
                                location=jl,
                                description=full_text,
                                url=ju,
                                platform="linkedin",
                                posted_date=posted,
                                easy_apply="Easy Apply" in full_text,
                                experience=exp,
                            )
                        )
                    except Exception:
                        continue

                if len(jobs) >= max_jobs:
                    break
                time.sleep(0.7)
            except Exception as e:
                logger.warning(f"LinkedIn error: {e}")

        return jobs

    def _search_indeed(
        self,
        title: str,
        location: str,
        max_jobs: int = 50,
        posted_within_days: int = 14,
    ) -> list[JobListing]:
        jobs: list[JobListing] = []
        starts = [0, 10, 20, 30, 40]
        forage = min(max(posted_within_days, 1), 30)

        for start in starts:
            params = {"q": title, "l": location, "sort": "date", "fromage": forage, "start": start}
            url = f"https://www.indeed.com/jobs?{urlencode(params)}"

            try:
                resp = self.session.get(url, timeout=15)
                if resp.status_code != 200:
                    continue

                soup = BeautifulSoup(resp.text, "html.parser")
                cards = soup.find_all("div", class_=re.compile(r"job_seen_beacon|cardOutline"))

                for card in cards:
                    try:
                        t_el = card.find("h2", class_=re.compile(r"jobTitle"))
                        if not t_el:
                            continue

                        t_link = t_el.find("a") or t_el.find("span")
                        co_el = card.find("span", attrs={"data-testid": "company-name"})
                        loc_el = card.find("div", attrs={"data-testid": "text-location"})
                        date_el = card.find("span", attrs={"data-testid": "myJobsStateDate"}) or card.find(
                            "span", class_=re.compile(r"date|metadata")
                        )

                        jt = t_link.get_text(strip=True) if t_link else ""
                        co = co_el.get_text(strip=True) if co_el else ""
                        jl = loc_el.get_text(strip=True) if loc_el else location
                        posted = date_el.get_text(" ", strip=True) if date_el else ""

                        link = t_el.find("a")
                        ju = f"https://www.indeed.com{link.get('href', '')}" if link else ""
                        if not jt or not co:
                            continue

                        snip_el = card.find("div", class_=re.compile(r"job-snippet"))
                        desc = snip_el.get_text(" ", strip=True) if snip_el else ""
                        exp = self._extract_experience(f"{jt} {desc}")

                        jobs.append(
                            JobListing(
                                job_id=JobListing.generate_id(ju, jt, co),
                                title=jt,
                                company=co,
                                location=jl,
                                description=desc,
                                url=ju,
                                platform="indeed",
                                posted_date=posted,
                                easy_apply="Easily apply" in card.get_text(),
                                experience=exp,
                            )
                        )
                    except Exception:
                        continue

                if len(jobs) >= max_jobs:
                    break
                time.sleep(0.7)
            except Exception as e:
                logger.warning(f"Indeed error: {e}")

        return jobs

    def _search_naukri(
        self,
        title: str,
        location: str,
        max_jobs: int = 50,
        min_experience: int = 0,
    ) -> list[JobListing]:
        jobs: list[JobListing] = []
        slug_t = title.lower().replace(" ", "-")
        slug_l = location.lower().replace(" ", "-")
        url = f"https://www.naukri.com/{slug_t}-jobs-in-{slug_l}"

        for page in [1, 2, 3]:
            params = {"experience": str(min_experience), "k": title, "l": location, "pageNo": page}

            try:
                resp = self.session.get(url, params=params, timeout=15)
                if resp.status_code != 200:
                    continue

                soup = BeautifulSoup(resp.text, "html.parser")
                cards = soup.find_all("article", class_=re.compile(r"jobTuple"))
                if not cards:
                    cards = soup.find_all("div", class_=re.compile(r"srp-jobtuple|cust-job-tuple"))

                for card in cards:
                    try:
                        t_el = card.find("a", class_=re.compile(r"title"))
                        co_el = card.find("a", class_=re.compile(r"subTitle|comp-name"))
                        loc_el = card.find("span", class_=re.compile(r"locWdth|loc-wrap|ellipsis"))
                        sal_el = card.find("span", class_=re.compile(r"sal-wrap|salary"))
                        exp_el = card.find("span", class_=re.compile(r"expwdth|exp-wrap|experience"))
                        posted_el = card.find("span", class_=re.compile(r"job-post-day|date"))
                        desc_el = card.find("span", class_=re.compile(r"job-desc|ellipsis"))

                        jt = t_el.get_text(strip=True) if t_el else ""
                        co = co_el.get_text(strip=True) if co_el else ""
                        jl = loc_el.get_text(strip=True) if loc_el else location
                        sal = sal_el.get_text(strip=True) if sal_el else ""
                        ju = t_el.get("href", "") if t_el else ""
                        exp = exp_el.get_text(strip=True) if exp_el else self._extract_experience(jt)
                        posted = posted_el.get_text(" ", strip=True) if posted_el else ""
                        desc = desc_el.get_text(" ", strip=True) if desc_el else ""

                        if not jt or not co:
                            continue

                        jobs.append(
                            JobListing(
                                job_id=JobListing.generate_id(ju, jt, co),
                                title=jt,
                                company=co,
                                location=jl,
                                description=desc,
                                url=ju,
                                platform="naukri",
                                salary=sal,
                                posted_date=posted,
                                experience=exp,
                            )
                        )
                    except Exception:
                        continue

                if len(jobs) >= max_jobs:
                    break
                time.sleep(0.7)
            except Exception as e:
                logger.warning(f"Naukri error: {e}")

        return jobs

    def _deduplicate(self, jobs: list[JobListing]) -> list[JobListing]:
        seen = set()
        unique = []
        for j in jobs:
            if j.job_id not in seen:
                seen.add(j.job_id)
                unique.append(j)
        return unique

    def _extract_experience(self, text: str) -> str:
        if not text:
            return ""
        patterns = [
            r"(\d+\s*-\s*\d+\s*(?:years?|yrs?))",
            r"(\d+\+\s*(?:years?|yrs?))",
            r"((?:years?|yrs?)\s*[:\-]?\s*\d+\+?)",
        ]
        for pat in patterns:
            m = re.search(pat, text.lower())
            if m:
                return m.group(1).replace("yrs", "years")
        return ""

    def _experience_to_range(self, text: str) -> tuple[int | None, int | None]:
        t = (text or "").lower()
        m = re.search(r"(\d+)\s*-\s*(\d+)", t)
        if m:
            return int(m.group(1)), int(m.group(2))
        m = re.search(r"(\d+)\+", t)
        if m:
            v = int(m.group(1))
            return v, None
        m = re.search(r"(\d+)\s*(?:years?|yrs?)", t)
        if m:
            v = int(m.group(1))
            return v, v
        return None, None

    def _posted_within_window(self, posted: str, posted_within_days: int) -> bool:
        if not posted:
            return True
        t = posted.lower().strip()
        if "today" in t or "just now" in t:
            return True
        if "hour" in t or "minute" in t:
            return True
        m = re.search(r"(\d+)\s+day", t)
        if m:
            return int(m.group(1)) <= posted_within_days
        m = re.search(r"(\d+)\s+week", t)
        if m:
            return int(m.group(1)) * 7 <= posted_within_days
        try:
            d = datetime.fromisoformat(t[:10]).date()
            return d >= (datetime.utcnow().date() - timedelta(days=posted_within_days))
        except Exception:
            return True

    def _apply_filters(
        self,
        jobs: list[JobListing],
        posted_within_days: int,
        min_experience: int,
        max_experience: int,
    ) -> list[JobListing]:
        filtered = []
        for j in jobs:
            if not self._posted_within_window(j.posted_date, posted_within_days):
                continue
            lo, hi = self._experience_to_range(j.experience)
            if lo is not None and hi is not None and (hi < min_experience or lo > max_experience):
                continue
            if lo is not None and hi is None and lo > max_experience:
                continue
            filtered.append(j)
        return filtered
