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

        # Sort by timestamp descending
        sorted_jobs = sorted(
            list(master_dict.values()), 
            key=lambda x: x.get('timestamp', ''), 
            reverse=True
        )

        with open(self.output_file, "w", encoding="utf-8") as f:
            json.dump(sorted_jobs, f, indent=4, ensure_ascii=False)
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
            
            async def scrape_jd(card):
                try:
                    await card.scroll_into_view_if_needed()
                    title = (await card.locator("h3").first.inner_text()).strip()
                    company = (await card.locator("h4").first.inner_text()).strip()
                    link = await card.locator("a").first.get_attribute("href")
                    
                    # Deep Scrape JD in new tab
                    jd_page = await context.new_page()
                    await jd_page.goto(link, wait_until="domcontentloaded", timeout=30000)
                    await jd_page.wait_for_selector(".show-more-less-html__markup", timeout=10000)
                    full_jd = (await jd_page.locator(".show-more-less-html__markup").first.inner_text()).strip()
                    await jd_page.close()

                    return {
                        "job_hash": self._generate_job_hash(title, company),
                        "platform": "LinkedIn",
                        "keyword": self.keyword,
                        "title": title, "company": company, "location": self.location,
                        "link": link, "full_description": full_jd,
                        "score": 0,
                        "timestamp": datetime.now().isoformat()
                    }
                except:
                    return None

            # Scrape JDs in parallel with a limit
            semaphore = asyncio.Semaphore(3) # Limit concurrency to avoid blocking
            async def throttled_scrape_jd(card):
                async with semaphore:
                    return await scrape_jd(card)

            tasks = [throttled_scrape_jd(card) for card in job_cards[:self.max_jobs]]
            results = await asyncio.gather(*tasks)
            self.jobs = [r for r in results if r]
            print(f"--- [LinkedIn] Scraped {len(self.jobs)} jobs ---")
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
            
            async def scrape_jd(card):
                try:
                    title = (await card.locator("h2.jobTitle").inner_text()).strip()
                    company = (await card.locator("[data-testid='company-name']").inner_text()).strip()
                    
                    # Try to get the job link
                    link_elem = card.locator("h2.jobTitle a")
                    jk = await link_elem.get_attribute("data-jk")
                    link = f"https://in.indeed.com/viewjob?jk={jk}" if jk else page.url

                    jd_page = await context.new_page()
                    await jd_page.goto(link, wait_until="domcontentloaded", timeout=30000)
                    await jd_page.wait_for_selector("#jobDescriptionText", timeout=10000)
                    full_jd = (await jd_page.locator("#jobDescriptionText").inner_text()).strip()
                    await jd_page.close()

                    return {
                        "job_hash": self._generate_job_hash(title, company),
                        "platform": "Indeed",
                        "keyword": self.keyword,
                        "title": title, "company": company, "location": self.location,
                        "link": link, "full_description": full_jd,
                        "score": 0,
                        "timestamp": datetime.now().isoformat()
                    }
                except:
                    return None

            semaphore = asyncio.Semaphore(3)
            async def throttled_scrape_jd(card):
                async with semaphore:
                    return await scrape_jd(card)

            tasks = [throttled_scrape_jd(card) for card in job_cards[:self.max_jobs]]
            results = await asyncio.gather(*tasks)
            self.jobs = [r for r in results if r]
            print(f"--- [Indeed] Scraped {len(self.jobs)} jobs ---")
        finally:
            await page.close()
        return self.jobs

# --- NAUKRI MODULE ---
class NaukriScraper(BaseScraper):
    async def scrape(self, context):
        print(f"\n[Naukri] Starting search for {self.keyword}...")
        page = await context.new_page()
        k = self.keyword.replace(" ", "-")
        l = self.location.replace(" ", "-")
        search_url = f"https://www.naukri.com/{k}-jobs-in-{l}"
        
        try:
            await page.goto(search_url, wait_until="domcontentloaded", timeout=45000)
            await page.wait_for_timeout(5000) 
            
            job_cards = await page.locator("article.jobTuple, .srp-jobtuple-wrapper").all()
            
            async def scrape_jd(card):
                try:
                    title_elem = card.locator("a.title")
                    title = (await title_elem.inner_text()).strip()
                    company = (await card.locator("a.subTitle, a.comp-name").first.inner_text()).strip()
                    link = await title_elem.get_attribute("href")
                    
                    jd_page = await context.new_page()
                    await jd_page.goto(link, wait_until="domcontentloaded", timeout=30000)
                    try:
                        await jd_page.wait_for_selector(".dang-inner-html, .job-desc", timeout=10000)
                        full_jd = (await jd_page.locator(".dang-inner-html, .job-desc").first.inner_text()).strip()
                    except:
                        full_jd = (await jd_page.locator("body").inner_text()).strip()
                    await jd_page.close()

                    return {
                        "job_hash": self._generate_job_hash(title, company),
                        "platform": "Naukri",
                        "keyword": self.keyword,
                        "title": title, "company": company, "location": self.location,
                        "link": link, "full_description": full_jd[:2000],
                        "score": 0,
                        "timestamp": datetime.now().isoformat()
                    }
                except:
                    return None

            semaphore = asyncio.Semaphore(3)
            async def throttled_scrape_jd(card):
                async with semaphore:
                    return await scrape_jd(card)

            tasks = [throttled_scrape_jd(card) for card in job_cards[:self.max_jobs]]
            results = await asyncio.gather(*tasks)
            self.jobs = [r for r in results if r]
            print(f"--- [Naukri] Scraped {len(self.jobs)} jobs ---")
        except Exception as e:
            print(f"[Naukri] Error: {e}")
        finally:
            await page.close()
        return self.jobs

# --- GLASSDOOR MODULE ---
class GlassdoorScraper(BaseScraper):
    async def scrape(self, context):
        print(f"\n[Glassdoor] Starting search for {self.keyword}...")
        page = await context.new_page()
        search_url = f"https://www.glassdoor.co.in/Job/jobs.htm?sc.keyword={self.keyword}"
        
        try:
            await page.goto(search_url, wait_until="domcontentloaded", timeout=45000)
            await page.wait_for_timeout(5000)
            
            job_cards = await page.locator("li[data-test='jobListing'], .react-job-listing").all()
                
            async def scrape_jd(card):
                try:
                    title_elem = card.locator("a[data-test='job-link'], a.jobLink")
                    title = (await title_elem.first.inner_text()).strip()
                    company = (await card.locator(".EmployerProfile_employerName__Cq2s_, .job-search-8wag7x").first.inner_text()).strip()
                    link = await title_elem.first.get_attribute("href")
                    if link and link.startswith("/"): link = f"https://www.glassdoor.co.in{link}"
                    
                    jd_page = await context.new_page()
                    await jd_page.goto(link, wait_until="domcontentloaded", timeout=30000)
                    try:
                        await jd_page.wait_for_selector(".JobDetails_jobDescription__uW_fK, #JobDescriptionContainer", timeout=10000)
                        full_jd = (await jd_page.locator(".JobDetails_jobDescription__uW_fK, #JobDescriptionContainer").first.inner_text()).strip()
                    except:
                        full_jd = (await jd_page.locator("body").inner_text()).strip()
                    await jd_page.close()

                    return {
                        "job_hash": self._generate_job_hash(title, company),
                        "platform": "Glassdoor",
                        "keyword": self.keyword,
                        "title": title, "company": company, "location": self.location,
                        "link": link, "full_description": full_jd[:2000],
                        "score": 0,
                        "timestamp": datetime.now().isoformat()
                    }
                except:
                    return None

            semaphore = asyncio.Semaphore(3)
            async def throttled_scrape_jd(card):
                async with semaphore:
                    return await scrape_jd(card)

            tasks = [throttled_scrape_jd(card) for card in job_cards[:self.max_jobs]]
            results = await asyncio.gather(*tasks)
            self.jobs = [r for r in results if r]
            print(f"--- [Glassdoor] Scraped {len(self.jobs)} jobs ---")
        except Exception as e:
            print(f"[Glassdoor] Error: {e}")
        finally:
            await page.close()
        return self.jobs

# --- INTERNSHALA MODULE ---
class InternshalaScraper(BaseScraper):
    async def scrape(self, context):
        print(f"\n[Internshala] Starting search for {self.keyword}...")
        page = await context.new_page()
        k = self.keyword.replace(" ", "-").lower()
        search_url = f"https://internshala.com/jobs/keywords-{k}/"
        
        try:
            await page.goto(search_url, wait_until="domcontentloaded", timeout=45000)
            await page.wait_for_timeout(3000)
            
            job_cards = await page.locator(".individual_internship").all()
            
            async def scrape_jd(card):
                try:
                    title = (await card.locator(".heading_4_5 a, .job-title-href").first.inner_text()).strip()
                    company = (await card.locator(".company_name").first.inner_text()).strip()
                    link_suffix = await card.locator(".heading_4_5 a, .job-title-href").first.get_attribute("href")
                    link = f"https://internshala.com{link_suffix}" if link_suffix.startswith("/") else link_suffix
                    
                    jd_page = await context.new_page()
                    await jd_page.goto(link, wait_until="domcontentloaded", timeout=30000)
                    try:
                        await jd_page.wait_for_selector(".detail_view", timeout=10000)
                        full_jd = (await jd_page.locator(".detail_view").first.inner_text()).strip()
                    except:
                        full_jd = (await jd_page.locator("body").inner_text()).strip()
                    await jd_page.close()

                    return {
                        "job_hash": self._generate_job_hash(title, company),
                        "platform": "Internshala",
                        "keyword": self.keyword,
                        "title": title, "company": company, "location": self.location,
                        "link": link, "full_description": full_jd[:2000],
                        "score": 0,
                        "timestamp": datetime.now().isoformat()
                    }
                except:
                    return None

            semaphore = asyncio.Semaphore(3)
            async def throttled_scrape_jd(card):
                async with semaphore:
                    return await scrape_jd(card)

            tasks = [throttled_scrape_jd(card) for card in job_cards[:self.max_jobs]]
            results = await asyncio.gather(*tasks)
            self.jobs = [r for r in results if r]
            print(f"--- [Internshala] Scraped {len(self.jobs)} jobs ---")
        except Exception as e:
            print(f"[Internshala] Error: {e}")
        finally:
            await page.close()
        return self.jobs

# --- APNA MODULE ---
class ApnaScraper(BaseScraper):
    async def scrape(self, context):
        print(f"\n[Apna] Starting search for {self.keyword}...")
        page = await context.new_page()
        search_url = f"https://apna.co/jobs?search={self.keyword}&location={self.location}"
        
        try:
            await page.goto(search_url, wait_until="domcontentloaded", timeout=45000)
            await page.wait_for_timeout(5000)
            
            job_cards = await page.locator("a[href*='/job/']").all()
            
            async def scrape_jd(card):
                try:
                    title = (await card.locator("h3").first.inner_text()).strip()
                    company = (await card.locator("p").nth(0).inner_text()).strip()
                    link = await card.get_attribute("href")
                    if link and link.startswith("/"): link = f"https://apna.co{link}"
                    
                    jd_page = await context.new_page()
                    await jd_page.goto(link, wait_until="domcontentloaded", timeout=30000)
                    full_jd = (await jd_page.locator("body").inner_text()).strip()
                    await jd_page.close()

                    return {
                        "job_hash": self._generate_job_hash(title, company),
                        "platform": "Apna",
                        "keyword": self.keyword,
                        "title": title, "company": company, "location": self.location,
                        "link": link, "full_description": full_jd[:2000],
                        "score": 0,
                        "timestamp": datetime.now().isoformat()
                    }
                except:
                    return None

            semaphore = asyncio.Semaphore(3)
            async def throttled_scrape_jd(card):
                async with semaphore:
                    return await scrape_jd(card)

            tasks = [throttled_scrape_jd(card) for card in job_cards[:self.max_jobs]]
            results = await asyncio.gather(*tasks)
            self.jobs = [r for r in results if r]
            print(f"--- [Apna] Scraped {len(self.jobs)} jobs ---")
        except Exception as e:
            print(f"[Apna] Error: {e}")
        finally:
            await page.close()
        return self.jobs

# --- PLACEMENTINDIA MODULE ---
class PlacementIndiaScraper(BaseScraper):
    async def scrape(self, context):
        print(f"\n[PlacementIndia] Starting search for {self.keyword}...")
        page = await context.new_page()
        search_url = f"https://www.placementindia.com/job-search/search.php?keyword={self.keyword}&location={self.location}"
        
        try:
            await page.goto(search_url, wait_until="domcontentloaded", timeout=45000)
            await page.wait_for_timeout(3000)
            
            job_cards = await page.locator(".job-box").all()
            
            async def scrape_jd(card):
                try:
                    title_elem = card.locator("h2.job-title a")
                    title = (await title_elem.inner_text()).strip()
                    company = (await card.locator(".company-name").inner_text()).strip()
                    link = await title_elem.get_attribute("href")
                    
                    jd_page = await context.new_page()
                    await jd_page.goto(link, wait_until="domcontentloaded", timeout=30000)
                    full_jd = (await jd_page.locator("body").inner_text()).strip()
                    await jd_page.close()

                    return {
                        "job_hash": self._generate_job_hash(title, company),
                        "platform": "PlacementIndia",
                        "keyword": self.keyword,
                        "title": title, "company": company, "location": self.location,
                        "link": link, "full_description": full_jd[:2000],
                        "score": 0,
                        "timestamp": datetime.now().isoformat()
                    }
                except:
                    return None

            semaphore = asyncio.Semaphore(3)
            async def throttled_scrape_jd(card):
                async with semaphore:
                    return await scrape_jd(card)

            tasks = [throttled_scrape_jd(card) for card in job_cards[:self.max_jobs]]
            results = await asyncio.gather(*tasks)
            self.jobs = [r for r in results if r]
            print(f"--- [PlacementIndia] Scraped {len(self.jobs)} jobs ---")
        except Exception as e:
            print(f"[PlacementIndia] Error: {e}")
        finally:
            await page.close()
        return self.jobs

# --- MAIN COORDINATOR ---
async def main(keyword: str, location: str, max_jobs: int):
    # Divide total jobs among 7 scrapers, ensuring at least 2 per platform to get a decent spread
    scrapers_classes = [
        LinkedInScraper, 
        IndeedScraper, 
        NaukriScraper, 
        GlassdoorScraper, 
        InternshalaScraper, 
        ApnaScraper, 
        PlacementIndiaScraper
    ]
    max_per_platform = max_jobs

    async with Stealth().use_async(async_playwright()) as p:
        browser = await p.chromium.launch(headless=True) 
        context = await browser.new_context(
            viewport={'width': 1280, 'height': 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
        )
        
        # Initialize scrapers
        scrapers = [cls(keyword, location, max_per_platform) for cls in scrapers_classes]
        
        print(f"--- Launching parallel scrapers for {keyword} in {location} across {len(scrapers)} platforms ---")
        
        # Run scrapers concurrently
        tasks = [scraper.scrape(context) for scraper in scrapers]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Save results safely
        for res, scraper in zip(results, scrapers):
            if isinstance(res, list):
                scraper.save_results(res)
            else:
                print(f"Error in {scraper.__class__.__name__}: {res}")

        await browser.close()
        print("\nAll platforms processed. Check data/master_scraped_jobs.json")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Scrape Jobs")
    parser.add_argument("--keyword", type=str, default="Web Developer", help="Job search keyword")
    parser.add_argument("--location", type=str, default="India", help="Job search location")
    parser.add_argument("--max_jobs", type=int, default=30, help="Maximum number of jobs to scrape overall")
    args = parser.parse_args()

    asyncio.run(main(args.keyword, args.location, args.max_jobs))