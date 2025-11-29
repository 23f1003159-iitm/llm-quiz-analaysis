import os
import re
from playwright.async_api import Page
from urllib.parse import urljoin, urlparse

DOWNLOAD_DIR = "downloads"


class SmartScraper:
    """Intelligent web scraper with download and API call tracking"""
    
    def __init__(self, page: Page):
        self.page = page
        self.api_calls = []
        self.downloaded_files = []
        
    async def setup(self):
        """Initialize scraper with event handlers"""
        os.makedirs(DOWNLOAD_DIR, exist_ok=True)
        self.page.on("download", self._handle_download)
        self.page.on("response", self._handle_response)

    async def _handle_download(self, download):
        """Handle file downloads"""
        try:
            filename = download.suggested_filename
            path = os.path.join(DOWNLOAD_DIR, filename)
            await download.save_as(path)
            if filename not in self.downloaded_files:
                self.downloaded_files.append(filename)
            print(f"  📥 Auto-downloaded: {filename}")
        except Exception as e:
            print(f"  ⚠️ Download failed: {e}")

    async def _handle_response(self, response):
        """Track API responses for potential data sources"""
        try:
            content_type = response.headers.get("content-type", "")
            if "json" in content_type or "csv" in content_type or "xml" in content_type:
                url = response.url
                if len(url) < 500:  # Avoid tracking very long URLs
                    try:
                        if "json" in content_type:
                            data = await response.json()
                            snippet = str(data)[:300]
                        else:
                            snippet = (await response.text())[:300]
                        
                        self.api_calls.append({
                            "url": url,
                            "content_type": content_type,
                            "snippet": snippet
                        })
                    except:
                        pass
        except:
            pass

    async def get_page_context(self) -> dict:
        """
        Extract comprehensive context from the current page.
        
        Returns dict with:
            - text: visible page text
            - links: list of links with text and href
            - api_history: recent API calls detected
            - downloaded_files: files that were downloaded
        """
        # Extract all links
        links = await self.page.evaluate("""() => {
            const links = Array.from(document.querySelectorAll('a[href]'));
            return links.map(a => ({
                text: (a.innerText || a.textContent || '').trim().substring(0, 100),
                href: a.href
            })).filter(l => l.href && !l.href.startsWith('javascript:'));
        }""")
        
        # Extract page text
        try:
            text = await self.page.evaluate("""() => {
                // Get text content, preserving some structure
                const body = document.body;
                if (!body) return '';
                
                // Remove script and style elements from consideration
                const clone = body.cloneNode(true);
                const scripts = clone.querySelectorAll('script, style, noscript');
                scripts.forEach(s => s.remove());
                
                return clone.innerText || clone.textContent || '';
            }""")
        except:
            text = ""
        
        # Extract any visible code blocks or pre-formatted text
        try:
            code_blocks = await self.page.evaluate("""() => {
                const blocks = document.querySelectorAll('pre, code');
                return Array.from(blocks).map(b => b.textContent).join('\\n---\\n');
            }""")
            if code_blocks:
                text += "\n\n=== CODE/PRE BLOCKS ===\n" + code_blocks
        except:
            pass
        
        # Get list of actually downloaded files
        actual_files = []
        if os.path.exists(DOWNLOAD_DIR):
            actual_files = os.listdir(DOWNLOAD_DIR)
        
        # Merge tracked downloads with actual files
        all_files = list(set(self.downloaded_files + actual_files))

        return {
            "text": text.strip(),
            "links": links[:30],  # Limit to 30 most relevant links
            "api_history": self.api_calls[-10:],  # Last 10 API calls
            "downloaded_files": all_files
        }
    
    async def download_file_from_url(self, url: str, filename: str = None) -> str:
        """
        Programmatically download a file from URL.
        
        Returns the local filepath or None if failed.
        """
        try:
            import httpx
            
            async with httpx.AsyncClient(follow_redirects=True) as client:
                resp = await client.get(url, timeout=30.0)
                
                if resp.status_code == 200:
                    # Determine filename
                    if not filename:
                        # Try to get from Content-Disposition header
                        cd = resp.headers.get("content-disposition", "")
                        if "filename=" in cd:
                            filename = cd.split("filename=")[-1].strip('"\'')
                        else:
                            # Use URL path
                            filename = os.path.basename(urlparse(url).path) or "downloaded_file"
                    
                    filepath = os.path.join(DOWNLOAD_DIR, filename)
                    with open(filepath, "wb") as f:
                        f.write(resp.content)
                    
                    if filename not in self.downloaded_files:
                        self.downloaded_files.append(filename)
                    
                    return filepath
        except Exception as e:
            print(f"  ⚠️ Failed to download {url}: {e}")
        
        return None