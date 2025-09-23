# intelligent_crawler.py
import asyncio
import os
import re
from playwright.async_api import async_playwright, Page, TimeoutError as PlaywrightTimeoutError
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import config
from utils.formFiller import FormFiller

class IntelligentCrawler:
    def __init__(self):
        self.domain = urlparse(config.START_URL_AFTER_LOGIN).netloc
        # === KEY CHANGE: Simplified state tracking ===
        self.processed_urls = set() # This will be our single source of truth for visited URLs
        self.site_data = {}
        self.form_filler = FormFiller()

    async def login(self, page: Page):
        # This login function is correct and does not need changes.
        print("="*60)
        print("MANUAL LOGIN REQUIRED")
        print("="*60)
        if hasattr(config, 'LOGIN_URL') and config.LOGIN_URL:
            await page.goto(config.LOGIN_URL, wait_until="networkidle")
            print(f"\nBrowser window is open at: {config.LOGIN_URL}")
        else:
            print(f"\nBrowser window is open. Please navigate to the login page.")
        print("1. Please complete the login process manually in the browser.")
        print(f"2. Navigate to the main dashboard or starting page (e.g., {config.START_URL_AFTER_LOGIN}).")
        input("\n>>> Once you are logged in and on the main page, press Enter here to continue...")
        try:
            print("\nResuming automation. Verifying login success...")
            success_locator = None
            indicator_description = ""
            if hasattr(config, 'LOGIN_SUCCESS_INDICATOR_TEXT') and config.LOGIN_SUCCESS_INDICATOR_TEXT:
                indicator_description = f"text '{config.LOGIN_SUCCESS_INDICATOR_TEXT}'"
                success_locator = page.get_by_text(re.compile(config.LOGIN_SUCCESS_INDICATOR_TEXT, re.IGNORECASE)).first
            elif hasattr(config, 'LOGIN_SUCCESS_INDICATOR_SELECTOR') and config.LOGIN_SUCCESS_INDICATOR_SELECTOR:
                indicator_description = f"selector '{config.LOGIN_SUCCESS_INDICATOR_SELECTOR}'"
                success_locator = page.locator(config.LOGIN_SUCCESS_INDICATOR_SELECTOR)
            else:
                print("! WARNING: No success indicator is configured. Assuming login was successful.")
                return True
            print(f"  - Waiting for success indicator ({indicator_description})...")
            await success_locator.wait_for(state="visible", timeout=10000)
            print("  - Success indicator found. Waiting for page to be fully stable...")
            await page.wait_for_load_state('networkidle', timeout=10000)
            print("Login confirmed! Starting automated exploration.")
            return True
        except Exception as e:
            print("-" * 60)
            print("LOGIN VERIFICATION FAILED!")
            print(f"Could not find the success indicator ({indicator_description}) on the current page.")
            print(f"Current URL is: {page.url}")
            print("Please ensure you have navigated to the correct page after login and that the indicator in config.py is correct.")
            print("-" * 60)
            return False

    def _parse_content(self, html: str):
        soup = BeautifulSoup(html, "html.parser")
        for script_or_style in soup(["script", "style"]):
            script_or_style.decompose()
        return ' '.join(soup.stripped_strings)

    async def explore(self):
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context()
            page = await context.new_page()

            if not await self.login(page):
                print("Cannot proceed with exploration. Exiting.")
                await browser.close()
                return {}

            # Use a list as a First-In, First-Out (FIFO) queue
            urls_to_visit = [page.url]
            
            # === KEY CHANGE: Robust Loop Logic ===
            while urls_to_visit:
                current_url = urls_to_visit.pop(0) # Get the next URL from the front of the queue
                
                # If we have already processed this URL, skip it entirely.
                # This is the primary defense against loops.
                if current_url in self.processed_urls:
                    continue
                
                try:
                    if page.url != current_url:
                        print(f"\nNavigating to: {current_url}")
                        await page.goto(current_url, wait_until="networkidle", timeout=60000)
                    else:
                        print(f"\nProcessing current page: {current_url}")
                    
                    # Mark this URL as processed so we never visit it again.
                    self.processed_urls.add(current_url)
                    
                    print(f"  - New state discovered. Processing...")
                    page_content = await page.content()
                    text = self._parse_content(page_content)
                    self.site_data[current_url] = {"text": text, "links": set()}

                    # Discover all new, unseen links on the page
                    links = await page.locator('a[href]').all()
                    for link in links:
                        href = await link.get_attribute('href')
                        if href:
                            full_url = urljoin(current_url, href).split('#')[0] # Normalize URL
                            
                            # Check conditions to add the link to our queue
                            is_internal = urlparse(full_url).netloc == self.domain
                            is_web_link = full_url.startswith('http')
                            is_new = full_url not in self.processed_urls and full_url not in urls_to_visit
                            
                            if is_internal and is_web_link and is_new:
                                urls_to_visit.append(full_url)
                                self.site_data[current_url]['links'].add(full_url)
                
                except Exception as e:
                    print(f"  - ERROR processing {current_url}: {e}")
                    # Make sure to mark even failed URLs as processed to avoid retrying them
                    self.processed_urls.add(current_url)
                    continue

            # Convert sets to lists for the final JSON output
            for url in self.site_data:
                self.site_data[url]['links'] = list(self.site_data[url]['links'])
                
            print("\n--- Exploration Finished ---")
            await browser.close()
            return self.site_data