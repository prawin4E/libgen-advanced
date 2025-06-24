from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup
from typing import Optional, Tuple
import time
from app.utils.logs import logger

class LibgenDownloader:
    """
    A class to handle fetching direct download URLs from LibGen.
    """

    def __init__(self, base_url: str = "https://libgen.li"):
        self.base_url = base_url
        self.session = requests.Session()

    def check_link(self, url: str, timeout: int = 30) -> bool:
        """
        Check if a link is accessible using HEAD request
        Returns True if link is working, False otherwise
        """
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.head(url, headers=headers, timeout=timeout, allow_redirects=True)
            return 200 <= response.status_code < 300
            
        except:
            return False

    def get_direct_download_url(self, md5: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Fetch the direct download URL and cover image URL for a given LibGen MD5 hash.

        Args:
            md5 (str): The MD5 hash of the book.

        Returns:
            Tuple[Optional[str], Optional[str]]: A tuple of direct download URL and cover image URL if found.
        """
        ads_url = f"{self.base_url}/ads.php?md5={md5}"

        try:
            response = self.session.get(ads_url, timeout=30)
            if response.status_code != 200:
                logger.error(f"Failed to open book page for MD5: {md5}")
                return None, None

            soup = BeautifulSoup(response.text, "html.parser")
            all_links = soup.find_all("a", href=True)

            direct_download_url = None
            cover_image_url = None
            img_td = soup.find("td", {"rowspan": "2"})
            if img_td:
                img = img_td.find("img")
                if img and img.get("src"):
                    img_src = img["src"]
                    if not img_src.startswith("http"):
                        img_src = urljoin(self.base_url, img_src)
                    cover_image_url = img_src

            for link in all_links:
                href = link["href"]
                if "get.php" in href and "key=" in href:
                    href = href.lstrip("/")
                    
                    cdn2_url = urljoin("https://cdn2.booksdl.lc/", href)
                    libgen_url = urljoin("https://libgen.li/", href)
                    
                    if self.check_link(cdn2_url):
                        direct_download_url = cdn2_url
                        logger.info(f"Using cdn2.booksdl.lc for MD5: {md5}")
                        break
                    elif self.check_link(libgen_url):
                        direct_download_url = libgen_url
                        logger.info(f"Using libgen.li for MD5: {md5}")
                        break

            if not direct_download_url:
                logger.error(f"No working direct download link found for MD5: {md5}")

            return direct_download_url, cover_image_url

        except Exception as e:
            logger.error(f"Unexpected error for MD5 {md5}: {e}")
            return None, None

downloader = LibgenDownloader()