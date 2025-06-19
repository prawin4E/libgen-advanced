
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup
from typing import Optional, Tuple
from app.utils.logs import logger

class LibgenDownloader:
    """
    A class to handle fetching direct download URLs from LibGen.
    """

    def __init__(self, base_url: str = "https://libgen.li"):
        self.base_url = base_url
        self.session = requests.Session()

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

            # Try to find the cover image
            img_td = soup.find("td", {"rowspan": "2"})
            if img_td:
                img = img_td.find("img")
                if img and img.get("src"):
                    img_src = img["src"]
                    if not img_src.startswith("http"):
                        img_src = urljoin(self.base_url, img_src)
                    cover_image_url = img_src

            # Try to find the direct download link
            for link in all_links:
                href = link["href"]
                if "get.php" in href and "key=" in href:
                    href = href.lstrip("/")
                    direct_download_url = urljoin("https://cdn2.booksdl.lc/", href)
                    break

            if not direct_download_url:
                logger.error(f"Direct download link with key not found for MD5: {md5}")

            return direct_download_url, cover_image_url

        except Exception as e:
            logger.error(f"Unexpected error for MD5 {md5}: {e}")
            return None, None

downloader = LibgenDownloader()