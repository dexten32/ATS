import asyncio
import random
import json
import hashlib
import os
from datetime import datetime
from typing import List, Dict, Any
from playwright.async_api import async_playwright
from playwright_stealth import Stealth

# --- BASE SCRAPER CLASS ---
class BaseScraper:
    def __init__(self, keyword: str, location: str, max_jobs: int):
        self.keyword = keyword
        self.location = location
        self.max_jobs = max_jobs
        self.jobs = []
        
        # Ensure data directory exists
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.base_dir = os.path.dirname(self.script_dir)
        self.output_dir = os.path.join(self.base_dir, "data")
        os.makedirs(self.output_dir, exist_ok=True)
        self.output_file = os.path.join(self.output_dir, "master_scraped_jobs.json")

    def _generate_job_hash(self, title: str, company: str) -> str:
        data = f"{title.lower()}|{company.lower()}|{self.location.lower()}".encode()
        return hashlib.sha256(data).hexdigest()

    def save_results(self, new_jobs: List[Dict]):
        # Load existing jobs to prevent overwriting other platforms
        existing_jobs = []
        if os.path.exists(self.output_file):
            try:
                with open(self.output_file, "r", encoding="utf-8") as f:
                    existing_jobs = json.load(f)
            except: existing_jobs = []

        # Use a dict to deduplicate by hash
        master_dict = {j['job_hash']: j for j in existing_jobs}
        for nj in new_jobs:
            master_dict[nj['job_hash']] = nj

        with open(self.output_file, "w", encoding="utf-8") as f:
            json.dump(list(master_dict.values()), f, indent=4, ensure_ascii=False)
        print(f"--- Saved results to {self.output_file} ---")

# --- LINKEDIN MODULE ---
class LinkedInScraper(BaseScraper):
    async def scrape(self, context):
        print(f"\n[LinkedIn] Starting search for {self.keyword}...")
        page = await context.new_page()
        search_url = f"https://www.linkedin.com/jobs/search?keywords={self.keyword}&location={self.location}&f_TPR=r86400"
        
        try:
            await page.goto(search_url, wait_until="domcontentloaded", timeout=60000)
            await page.wait_for_selector(".base-card", timeout=15000)
            
            job_cards = await page.locator(".base-card, .job-search-card").all()
            for i, card in enumerate(job_cards[:self.max_jobs]):
                try:
                    await card.scroll_into_view_if_needed()
                    title = (await card.locator("h3").first.inner_text()).strip()
                    company = (await card.locator("h4").first.inner_text()).strip()
                    link = await card.locator("a").first.get_attribute("href")
                    
                    # Deep Scrape JD in new tab
                    jd_page = await context.new_page()
                    await jd_page.goto(link, wait_until="domcontentloaded")
                    await jd_page.wait_for_selector(".show-more-less-html__markup", timeout=10000)
                    full_jd = (await jd_page.locator(".show-more-less-html__markup").first.inner_text()).strip()
                    await jd_page.close()

                    self.jobs.append({
                        "job_hash": self._generate_job_hash(title, company),
                        "platform": "LinkedIn",
                        "keyword": self.keyword,
                        "title": title, "company": company, "location": self.location,
                        "link": link, "full_description": full_jd,
                        "score": 0,
                        "timestamp": datetime.now().isoformat()
                    })
                    print(f"   ✓ [LinkedIn] {title}")
                    await page.wait_for_timeout(random.randint(2000, 4000))
                except: continue
        finally:
            await page.close()
        return self.jobs

# --- INDEED MODULE ---
class IndeedScraper(BaseScraper):
    async def scrape(self, context):
        print(f"\n[Indeed] Starting search for {self.keyword}...")
        page = await context.new_page()
        # Indeed URL format
        search_url = f"https://in.indeed.com/jobs?q={self.keyword}&l={self.location}&fromage=1"
        
        try:
            await page.goto(search_url, wait_until="domcontentloaded")
            await page.wait_for_timeout(5000)
            
            # Indeed Job Cards use 'job_seen_beacon'
            job_cards = await page.locator(".job_seen_beacon").all()
            for i, card in enumerate(job_cards[:self.max_jobs]):
                try:
                    title = (await card.locator("h2.jobTitle").inner_text()).strip()
                    company = (await card.locator("[data-testid='company-name']").inner_text()).strip()
                    # Indeed requires a bit of click logic to see JD on the same page
                    await card.click()
                    await page.wait_for_selector("#jobDescriptionText", timeout=10000)
                    full_jd = (await page.locator("#jobDescriptionText").inner_text()).strip()

                    self.jobs.append({
                        "job_hash": self._generate_job_hash(title, company),
                        "platform": "Indeed",
                        "keyword": self.keyword,
                        "title": title, "company": company, "location": self.location,
                        "link": page.url, "full_description": full_jd,
                        "score": 0,
                        "timestamp": datetime.now().isoformat()
                    })
                    print(f"   ✓ [Indeed] {title}")
                    await page.wait_for_timeout(random.randint(2000, 4000))
                except: continue
        finally:
            await page.close()
        return self.jobs

# --- MAIN COORDINATOR ---
async def main(keyword: str, location: str, max_jobs: int):
    max_per_platform = max(1, max_jobs // 2)

    async with Stealth().use_async(async_playwright()) as p:
        browser = await p.chromium.launch(headless=False) # Change to True for background
        context = await browser.new_context(viewport={'width': 1280, 'height': 800})
        
        # 1. Scrape LinkedIn
        li_scraper = LinkedInScraper(keyword, location, max_per_platform)
        li_results = await li_scraper.scrape(context)
        li_scraper.save_results(li_results)

        # 2. Scrape Indeed
        in_scraper = IndeedScraper(keyword, location, max_per_platform)
        in_results = await in_scraper.scrape(context)
        in_scraper.save_results(in_results)

        await browser.close()
        print("\nAll platforms processed. Check data/master_scraped_jobs.json")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Scrape Jobs")
    parser.add_argument("--keyword", type=str, default="Web Developer", help="Job search keyword")
    parser.add_argument("--location", type=str, default="India", help="Job search location")
    parser.add_argument("--max_jobs", type=int, default=10, help="Maximum number of jobs to scrape")
    args = parser.parse_args()

    asyncio.run(main(args.keyword, args.location, args.max_jobs))