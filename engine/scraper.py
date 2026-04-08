"""Lightweight job scraper using requests + BeautifulSoup. No browser automation."""

import re
import time
import logging
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

    def search(self, title: str, location: str, platforms: list[str] | None = None) -> list[JobListing]:
        if platforms is None:
            platforms = ["linkedin", "indeed", "naukri"]
        all_jobs = []
        for platform in platforms:
            try:
                if platform == "linkedin":
                    all_jobs.extend(self._search_linkedin(title, location))
                elif platform == "indeed":
                    all_jobs.extend(self._search_indeed(title, location))
                elif platform == "naukri":
                    all_jobs.extend(self._search_naukri(title, location))
                time.sleep(1.5)
            except Exception as e:
                logger.warning(f"{platform} search failed: {e}")
        return self._deduplicate(all_jobs)

    def _search_linkedin(self, title: str, location: str) -> list[JobListing]:
        jobs = []
        params = {
            "keywords": title, "location": location,
            "f_TPR": "r604800", "position": 1, "pageNum": 0,
        }
        url = f"https://www.linkedin.com/jobs/search/?{urlencode(params)}"
        try:
            resp = self.session.get(url, timeout=15)
            if resp.status_code != 200:
                return jobs
            soup = BeautifulSoup(resp.text, "html.parser")
            cards = soup.find_all("div", class_=re.compile(r"base-card|job-search-card"))
            for card in cards[:25]:
                try:
                    title_el = card.find("h3", class_=re.compile(r"base-search-card__title"))
                    company_el = card.find("h4", class_=re.compile(r"base-search-card__subtitle"))
                    link_el = card.find("a", class_=re.compile(r"base-card__full-link"))
                    loc_el = card.find("span", class_=re.compile(r"job-search-card__location"))
                    if not all([title_el, company_el, link_el]):
                        continue
                    jt = title_el.get_text(strip=True)
                    co = company_el.get_text(strip=True)
                    ju = link_el.get("href", "").split("?")[0]
                    jl = loc_el.get_text(strip=True) if loc_el else location
                    jobs.append(JobListing(
                        job_id=JobListing.generate_id(ju, jt, co),
                        title=jt, company=co, location=jl, description="",
                        url=ju, platform="linkedin",
                        easy_apply="Easy Apply" in card.get_text(),
                    ))
                except Exception:
                    continue
        except Exception as e:
            logger.warning(f"LinkedIn error: {e}")
        return jobs

    def _search_indeed(self, title: str, location: str) -> list[JobListing]:
        jobs = []
        params = {"q": title, "l": location, "sort": "date", "fromage": 7}
        url = f"https://www.indeed.com/jobs?{urlencode(params)}"
        try:
            resp = self.session.get(url, timeout=15)
            if resp.status_code != 200:
                return jobs
            soup = BeautifulSoup(resp.text, "html.parser")
            cards = soup.find_all("div", class_=re.compile(r"job_seen_beacon|cardOutline"))
            for card in cards[:25]:
                try:
                    t_el = card.find("h2", class_=re.compile(r"jobTitle"))
                    if not t_el:
                        continue
                    t_link = t_el.find("a") or t_el.find("span")
                    co_el = card.find("span", attrs={"data-testid": "company-name"})
                    loc_el = card.find("div", attrs={"data-testid": "text-location"})
                    jt = t_link.get_text(strip=True) if t_link else ""
                    co = co_el.get_text(strip=True) if co_el else ""
                    jl = loc_el.get_text(strip=True) if loc_el else location
                    link = t_el.find("a")
                    ju = f"https://www.indeed.com{link.get('href', '')}" if link else ""
                    if not jt or not co:
                        continue
                    snip_el = card.find("div", class_=re.compile(r"job-snippet"))
                    desc = snip_el.get_text(strip=True) if snip_el else ""
                    jobs.append(JobListing(
                        job_id=JobListing.generate_id(ju, jt, co),
                        title=jt, company=co, location=jl, description=desc,
                        url=ju, platform="indeed",
                        easy_apply="Easily apply" in card.get_text(),
                    ))
                except Exception:
                    continue
        except Exception as e:
            logger.warning(f"Indeed error: {e}")
        return jobs

    def _search_naukri(self, title: str, location: str) -> list[JobListing]:
        jobs = []
        slug_t = title.lower().replace(" ", "-")
        slug_l = location.lower().replace(" ", "-")
        url = f"https://www.naukri.com/{slug_t}-jobs-in-{slug_l}"
        try:
            resp = self.session.get(url, params={"experience": "5"}, timeout=15)
            if resp.status_code != 200:
                return jobs
            soup = BeautifulSoup(resp.text, "html.parser")
            cards = soup.find_all("article", class_=re.compile(r"jobTuple"))
            if not cards:
                cards = soup.find_all("div", class_=re.compile(r"srp-jobtuple|cust-job-tuple"))
            for card in cards[:25]:
                try:
                    t_el = card.find("a", class_=re.compile(r"title"))
                    co_el = card.find("a", class_=re.compile(r"subTitle|comp-name"))
                    loc_el = card.find("span", class_=re.compile(r"locWdth|loc-wrap|ellipsis"))
                    sal_el = card.find("span", class_=re.compile(r"sal-wrap|salary"))
                    jt = t_el.get_text(strip=True) if t_el else ""
                    co = co_el.get_text(strip=True) if co_el else ""
                    jl = loc_el.get_text(strip=True) if loc_el else location
                    sal = sal_el.get_text(strip=True) if sal_el else ""
                    ju = t_el.get("href", "") if t_el else ""
                    if not jt or not co:
                        continue
                    jobs.append(JobListing(
                        job_id=JobListing.generate_id(ju, jt, co),
                        title=jt, company=co, location=jl, description="",
                        url=ju, platform="naukri", salary=sal,
                    ))
                except Exception:
                    continue
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
