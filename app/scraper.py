import os
from playwright.async_api import Page

DOWNLOAD_DIR = "downloads"

class SmartScraper:
    def __init__(self, page: Page):
        self.page = page
        self.api_calls = []
        self.downloaded_files = []
        
    async def setup(self):
        os.makedirs(DOWNLOAD_DIR, exist_ok=True)
        self.page.on("download", self.handle_download)
        self.page.on("response", self.handle_response)

    async def handle_download(self, download):
        try:
            path = os.path.join(DOWNLOAD_DIR, download.suggested_filename)
            await download.save_as(path)
            self.downloaded_files.append(download.suggested_filename)
        except: pass

    async def handle_response(self, response):
        try:
            if "json" in response.headers.get("content-type", ""):
                if len(response.url) < 300: 
                    try:
                        data = await response.json()
                        self.api_calls.append({"url": response.url, "snippet": str(data)[:200]})
                    except: pass
        except: pass

    async def get_page_context(self):
        # EXTRACT LINKS: Critical for scraping tasks
        links = await self.page.evaluate("""() => {
            return Array.from(document.querySelectorAll('a')).map(a => ({text: a.innerText, href: a.href}));
        }""")
        
        try:
            text = await self.page.evaluate("document.body.innerText")
        except:
            text = ""

        actual_files = os.listdir(DOWNLOAD_DIR) if os.path.exists(DOWNLOAD_DIR) else []

        return {
            "text": text,
            "links": links[:20], # Top 20 links to avoid clutter
            "api_history": self.api_calls[-5:],
            "downloaded_files": actual_files
        }