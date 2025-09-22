# intelligent_crawler.py
import asyncio
import os
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import config
from form_filler import FormFiller

class IntelligentCrawler:
    def __init__(self):
        self.domain = urlparse(config.START_URL_AFTER_LOGIN).netloc
        self.visited_states = set()  # Use URL + content hash to identify unique states
        self.site_data = {}
        self.form_filler = FormFiller()

    async def login(self, page):
        """Performs the login action and verifies success."""
        print("Attempting to log in...")
        await page.goto(config.LOGIN_URL)
        await page.locator(config.USERNAME_SELECTOR).fill(config.USERNAME)
        await page.locator(config.PASSWORD_SELECTOR).fill(config.PASSWORD)
        await page.locator(config.SUBMIT_BUTTON_SELECTOR).click()
        
        try:
            # Wait for the success indicator to appear
            await page.wait_for_selector(config.LOGIN_SUCCESS_INDICATOR_SELECTOR, state="visible", timeout=10000)
            print("Login successful!")
            return True
        except Exception:
            print("Login failed. Check your credentials and selectors in config.py.")
            return False

    def _get_page_state(self, page_content: str) -> str:
        """Creates a unique identifier for a page's structure to detect changes."""
        # A simple hash of the structural tags can identify a unique page state
        soup = BeautifulSoup(page_content, "html.parser")
        structure = ''.join(tag.name for tag in soup.find_all(['h1', 'h2', 'button', 'form', 'a']))
        return str(hash(structure))

    def _parse_content(self, html: str):
        """Parses HTML to extract clean text."""
        soup = BeautifulSoup(html, "html.parser")
        for script_or_style in soup(["script", "style"]):
            script_or_style.decompose()
        return ' '.join(soup.stripped_strings)

    async def explore(self):
        """Main exploration logic."""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False) # Run in headed mode to observe
            context = await browser.new_context()
            page = await context.new_page()

            if not await self.login(page):
                await browser.close()
                return {}

            urls_to_visit = [config.START_URL_AFTER_LOGIN]
            
            while urls_to_visit:
                current_url = urls_to_visit.pop(0)
                
                try:
                    print(f"Navigating to: {current_url}")
                    await page.goto(current_url, wait_until="networkidle")
                    # Wait a moment for dynamic content to potentially load
                    await page.wait_for_timeout(2000) 
                except Exception as e:
                    print(f"Could not navigate to {current_url}: {e}")
                    continue

                page_content = await page.content()
                page_state_id = current_url + self._get_page_state(page_content)

                if page_state_id in self.visited_states:
                    print("  - State already visited. Skipping.")
                    continue
                
                self.visited_states.add(page_state_id)
                print(f"  - New state discovered. Processing...")

                text = self._parse_content(page_content)
                self.site_data[current_url] = {"text": text, "links": set()}

                # --- Discover and Execute Actions ---
                # 1. Links
                links = await page.locator('a[href]').all()
                for link in links:
                    href = await link.get_attribute('href')
                    if href:
                        full_url = urljoin(current_url, href)
                        if urlparse(full_url).netloc == self.domain and not full_url.startswith('mailto:'):
                            self.site_data[current_url]['links'].add(full_url)
                            if (full_url + self._get_page_state(page_content)) not in self.visited_states:
                                urls_to_visit.append(full_url)
                
                # 2. File Uploads
                upload_inputs = await page.locator('input[type="file"]').all()
                for upload_input in upload_inputs:
                    if await upload_input.is_visible():
                        print("  -> Found a file upload input.")
                        try:
                            # Find a sample image to upload
                            image_file = next((f for f in os.listdir(config.IMAGE_UPLOAD_FOLDER) if f.lower().endswith(('.png', '.jpg', '.jpeg'))), None)
                            if image_file:
                                await upload_input.set_input_files(os.path.join(config.IMAGE_UPLOAD_FOLDER, image_file))
                                print(f"    - Uploaded '{image_file}'.")
                        except Exception as e:
                            print(f"    - File upload failed: {e}")
                
                # 3. Forms
                forms = await page.locator('form').all()
                for form in forms:
                    if await form.is_visible():
                        self.form_filler.fill_form(form)
                        # Try to submit the form
                        submit_button = form.locator('button[type="submit"], input[type="submit"]').first
                        if await submit_button.is_visible():
                            print("    - Submitting form.")
                            await submit_button.click()
                            await page.wait_for_load_state('networkidle')
                            # Add the new URL to the queue if it's new and internal
                            new_url = page.url
                            if urlparse(new_url).netloc == self.domain:
                                self.site_data[current_url]['links'].add(new_url)
                                if (new_url + self._get_page_state(await page.content())) not in self.visited_states:
                                    urls_to_visit.append(new_url)
                                    # Go back to continue exploring the original page
                                    await page.goto(current_url)

            # Convert sets to lists for JSON serialization
            for url in self.site_data:
                self.site_data[url]['links'] = list(self.site_data[url]['links'])
                
            await browser.close()
            return self.site_data