import requests
from bs4 import BeautifulSoup
import pandas as pd
from urllib.parse import urljoin, quote
from app.utils.logs import logger
import time
import json


class LibGenScraper:
    def __init__(self, base_url="https://libgen.li"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def search(self, query, results_per_page=100):
        """
        Search for books on LibGen
        
        Args:
            query (str): Search query
            results_per_page (int): Number of results per page (25, 50, or 100)
        
        Returns:
            list: List of dictionaries containing book information
        """
        
        # Construct search URL
        search_url = f"{self.base_url}/index.php"
        
        # Parameters for the search
        params = {
            'req': query,
            'columns[]': ['t', 'a', 's', 'y', 'p', 'i'],  # title, author, series, year, publisher, isbn
            'objects[]': ['f', 'e', 's', 'a', 'p', 'w'],  # files, editions, series, authors, publishers, works
            'topics[]': ['l', 'c', 'f', 'a', 'm', 'r', 's'],  # libgen, comics, fiction, etc.
            'res': results_per_page,
            'filesuns': 'all'
        }
        
        # Convert lists to proper format for URL
        url_params = f"?req={quote(query)}"
        for col in params['columns[]']:
            url_params += f"&columns[]={col}"
        for obj in params['objects[]']:
            url_params += f"&objects[]={obj}"
        for topic in params['topics[]']:
            url_params += f"&topics[]={topic}"
        url_params += f"&res={results_per_page}&filesuns=all"
        
        full_url = search_url + url_params
        logger.info(f"Searching LibGen for: '{query}' (results/page: {results_per_page})")
        
        try:
            response = self.session.get(full_url)
            response.raise_for_status()
            return self._parse_search_results(response.text)
        except requests.RequestException as e:
            logger.error(f"Error fetching search results: {e}")
            return []
    
    def _parse_search_results(self, html):
        """Parse the search results HTML"""
        soup = BeautifulSoup(html, 'html.parser')
        books = []
        # Find the table by ID
        table = soup.find('table', {'id': 'tablelibgen'})
        
        if not table:
            logger.warning("No valid results table found in HTML.")
            # Try to find table with class
            table = soup.find('table', {'class': 'table table-striped'})
        
        if not table:
            all_tables = soup.find_all('table')
            print(f"DEBUG: Found {len(all_tables)} table(s) in the HTML")
            for i, t in enumerate(all_tables):
                print(f"DEBUG: Table {i} attributes: {t.attrs}")
            return books
        
        # Get all rows from tbody (skip header)
        tbody = table.find('tbody')
        if tbody:
            rows = tbody.find_all('tr')
        else:
            all_rows = table.find_all('tr')
            rows = all_rows[1:]  # Skip header
        for row_num, row in enumerate(rows):
            cells = row.find_all('td')
            
            # Let's check the actual structure with fewer cells
            if len(cells) < 9:  # Changed from 11 to 9
                continue
            
            # Let's print the first row's content to understand the structure
            book = {}
            
            # Based on the HTML structure, let's adjust the cell mapping
            # The table seems to have merged some columns
            
            # Cell 0: Contains ID, Title, Series, Author info
            first_cell = cells[0]
            
            # The first cell contains multiple pieces of information
            # Let's extract them carefully
            
            # Extract title from the first bold or link element
            title_elem = first_cell.find('b') or first_cell.find('a')
            if title_elem:
                book['title'] = title_elem.text.strip()
            
            # Extract ID from badge
            id_badge = first_cell.find('span', {'class': 'badge-secondary'})
            if id_badge:
                id_text = id_badge.text.strip()
                if ' ' in id_text:
                    book['id'] = id_text.split()[-1]
                else:
                    book['id'] = id_text
            
            # Extract series if present
            series_links = first_cell.find_all('a', href=lambda x: x and 'series.php' in x)
            if series_links:
                book['series'] = '; '.join([link.text.strip() for link in series_links])
            
            # Cell 1: Author(s)
            book['authors'] = cells[1].text.strip()
            
            # Cell 2: Publisher
            book['publisher'] = cells[2].text.strip()
            
            # Cell 3: Year
            book['year'] = cells[3].text.strip()
            
            # Cell 4: Language
            book['language'] = cells[4].text.strip()
            
            # Cell 5: Pages
            book['pages'] = cells[5].text.strip()
            
            # Cell 6: Size
            size_link = cells[6].find('a')
            if size_link:
                book['size'] = size_link.text.strip()
                book['file_url'] = urljoin(self.base_url, size_link.get('href', ''))
            else:
                book['size'] = cells[6].text.strip()
            
            # Cell 7: Extension
            book['extension'] = cells[7].text.strip()
            
            # Cell 8: Mirror links
            download_links = []
            if len(cells) > 8:
                links = cells[8].find_all('a')
                for link in links:
                    if link.get('href'):
                        href = link.get('href')
                        # Check if it's already a full URL or needs to be joined
                        full_url = href if href.startswith('http') else urljoin(self.base_url, href)
                        
                        download_links.append({
                            'text': link.text.strip(),
                            'url': full_url
                        })
                        
                        # Try to extract MD5 from the URL if it's a libgen download link
                        if '/ads.php?md5=' in full_url:
                            md5_match = full_url.split('md5=')[-1]
                            if md5_match:
                                book['md5'] = md5_match
                                # Build direct download URL
                                book['direct_download_url'] = f"{self.base_url}/get.php?md5={md5_match}"
            
            book['download_links'] = download_links
            
            books.append(book)
            
            # Cell 2: Publisher
            book['publisher'] = cells[2].text.strip()
            
            # Cell 3: Year
            book['year'] = cells[3].text.strip()
            
            # Cell 4: Language
            book['language'] = cells[4].text.strip()
            
            # Cell 5: Pages
            book['pages'] = cells[5].text.strip()
            
            # Cell 6: Size
            size_link = cells[6].find('a')
            if size_link:
                book['size'] = size_link.text.strip()
                book['file_url'] = urljoin(self.base_url, size_link.get('href', ''))
            else:
                book['size'] = cells[6].text.strip()
            
            # Cell 7: Extension
            book['extension'] = cells[7].text.strip()
            
            # Cell 8+: Mirror links
            download_links = []
            for i in range(8, len(cells)):
                links = cells[i].find_all('a')
                for link in links:
                    if link.get('href'):
                        download_links.append({
                            'text': link.text.strip(),
                            'url': link.get('href') if link.get('href').startswith('http') else urljoin(self.base_url, link.get('href'))
                        })
            book['download_links'] = download_links
            
            books.append(book)
        logger.info(f"Finished parsing. Total books found: {len(books)}")
        return books
    
    def save_to_csv(self, books, filepath):
        """Save the scraped books to a CSV file"""
        if not books:
            logger.warning("No books to save. Skipping CSV write.")
            return
        logger.info(f"Saving {len(books)} books to CSV: {filepath}")
        flattened_books = []
        for book in books:
            flat_book = book.copy()
            flat_book['download_links'] = '; '.join([link['text'] for link in book.get('download_links', [])])
            flattened_books.append(flat_book)
        
        df = pd.DataFrame(flattened_books)
        df.to_csv(filepath, index=False, encoding='utf-8')
        logger.info("CSV file saved successfully.")
    
    def convert_to_df(self, books):
        """Save the scraped books to a CSV file"""
        if not books:
            logger.warning("No books to convert to DataFrame.")
            return
        logger.info(f"Converting {len(books)} book(s) to DataFrame.")
        # Flatten the data for CSV
        flattened_books = []
        for book in books:
            flat_book = book.copy()
            # Convert download links to a simple string
            flat_book['download_links'] = '; '.join([link['text'] for link in book.get('download_links', [])])
            flattened_books.append(flat_book)
        
        df = pd.DataFrame(flattened_books)
        logger.info("DataFrame created successfully.")
        return df

    def save_to_json(self, books, filename='libgen_results.json'):
        """Save the scraped books to a JSON file"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(books, f, ensure_ascii=False, indent=2)