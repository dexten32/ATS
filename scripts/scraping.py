import asyncio
import random
import json
import hashlib
from typing import List, Dict, Any
from playwright.async_api import async_playwright
from playwright_stealth import Stealth

import os
class LinkedInScraper:
    def __init__(self, keyword: str, location: str, max_jobs: int = 10, output_file: str = None):
        self.keyword = keyword
        self.location = location
        self.max_jobs = max_jobs
        if output_file is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            self.output_file = os.path.join(base_dir, "data", "scraped_jobs.json")
        else:
            self.output_file = output_file
        self.jobs = []

    def _generate_job_hash(self, title: str, company: str) -> str:
        data = f"{title.lower()}|{company.lower()}|{self.location.lower()}".encode()
        return hashlib.sha256(data).hexdigest()

    async def _fetch_job_description(self, context: Any, link: str) -> str:
        detail_page = await context.new_page()
        full_jd = "Description not found"
        try:
            await detail_page.goto(link, wait_until="domcontentloaded", timeout=60000)
            jd_selector = ".show-more-less-html__markup, .description__text, section.description"
            await detail_page.wait_for_selector(jd_selector, timeout=10000)
            full_jd = (await detail_page.locator(jd_selector).first.inner_text()).strip()
        except Exception:
            pass
        finally:
            await detail_page.close()
        return full_jd

    def _save_jobs(self):
        with open(self.output_file, "w", encoding="utf-8") as f:
            json.dump(self.jobs, f, indent=4, ensure_ascii=False)
        print(f"\nSuccessfully saved {len(self.jobs)} jobs to {self.output_file}")

    async def scrape(self) -> List[Dict[str, str]]:
        async with Stealth().use_async(async_playwright()) as p:
            browser = await p.chromium.launch(headless=False) 
            context = await browser.new_context(viewport={'width': 1280, 'height': 800})
            page = await context.new_page()
            
            search_url = f"https://www.linkedin.com/jobs/search?keywords={self.keyword}&location={self.location}&f_TPR=r86400"
            print(f"Opening: {search_url}")
            
            try:
                await page.goto(search_url, wait_until="domcontentloaded", timeout=60000)
                await page.wait_for_selector(".base-card", timeout=15000)
            except Exception as e:
                print(f"Initial load failed: {e}")
                await browser.close()
                return []

            job_cards = await page.locator(".base-card, .job-search-card").all()
            print(f"Found {len(job_cards)} jobs. Starting deep extraction...")

            for i, card in enumerate(job_cards[:self.max_jobs]): 
                try:
                    await card.scroll_into_view_if_needed()
                    title = (await card.locator("h3, .base-search-card__title").first.inner_text()).strip()
                    company = (await card.locator("h4, .base-search-card__subtitle").first.inner_text()).strip()
                    link = await card.locator("a").first.get_attribute("href")
                    
                    print(f"[{i+1}] Fetching JD for: {title}...")

                    full_jd = await self._fetch_job_description(context, link)
                    job_id_hash = self._generate_job_hash(title, company)
                    
                    self.jobs.append({
                        "job_hash": job_id_hash,
                        "title": title,
                        "company": company,
                        "location": self.location,
                        "link": link,
                        "full_description": full_jd
                    })
                    
                    print(f"   ✓ Scraped successfully")
                    await page.wait_for_timeout(random.randint(2000, 4000))

                except Exception as e:
                    print(f"   ! Error on job {i+1}: {str(e)[:50]}")
                    continue

            self._save_jobs()
            await browser.close()
            return self.jobs

if __name__ == "__main__":
    scraper = LinkedInScraper(keyword="Web Developer", location="India", max_jobs=10)
    asyncio.run(scraper.scrape())