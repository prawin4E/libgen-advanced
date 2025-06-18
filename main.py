import requests
from bs4 import BeautifulSoup
import pandas as pd
from urllib.parse import urljoin, quote
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
        print(f"DEBUG: Starting search for '{query}'...")
        
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
        print(f"DEBUG: Full URL: {full_url}")
        
        try:
            print("DEBUG: Making HTTP request...")
            response = self.session.get(full_url)
            print(f"DEBUG: Response status code: {response.status_code}")
            response.raise_for_status()
            print(f"DEBUG: Response length: {len(response.text)} characters")
            return self._parse_search_results(response.text)
        except requests.RequestException as e:
            print(f"ERROR: Error fetching search results: {e}")
            return []
    
    def _parse_search_results(self, html):
        """Parse the search results HTML"""
        print("DEBUG: Starting to parse search results...")
        
        soup = BeautifulSoup(html, 'html.parser')
        books = []
        
        print("DEBUG: Looking for table with id='tablelibgen'...")
        # Find the table by ID
        table = soup.find('table', {'id': 'tablelibgen'})
        
        if not table:
            print("DEBUG: Table with id='tablelibgen' not found, trying class='table table-striped'...")
            # Try to find table with class
            table = soup.find('table', {'class': 'table table-striped'})
        
        if not table:
            print("DEBUG: No results table found at all!")
            print("DEBUG: Looking for any table tags...")
            all_tables = soup.find_all('table')
            print(f"DEBUG: Found {len(all_tables)} table(s) in the HTML")
            for i, t in enumerate(all_tables):
                print(f"DEBUG: Table {i} attributes: {t.attrs}")
            return books
        
        print(f"DEBUG: Found table! Attributes: {table.attrs}")
        
        # Get all rows from tbody (skip header)
        print("DEBUG: Looking for tbody...")
        tbody = table.find('tbody')
        if tbody:
            print("DEBUG: Found tbody, getting all tr elements...")
            rows = tbody.find_all('tr')
            print(f"DEBUG: Found {len(rows)} rows in tbody")
        else:
            print("DEBUG: No tbody found, getting all tr elements and skipping header...")
            all_rows = table.find_all('tr')
            print(f"DEBUG: Found {len(all_rows)} total rows")
            rows = all_rows[1:]  # Skip header
            print(f"DEBUG: After skipping header, {len(rows)} rows remain")
        
        print("DEBUG: Starting to process rows...")
        for row_num, row in enumerate(rows):
            print(f"\nDEBUG: Processing row {row_num + 1}...")
            cells = row.find_all('td')
            print(f"DEBUG: Row {row_num + 1} has {len(cells)} cells")
            
            # Let's check the actual structure with fewer cells
            if len(cells) < 9:  # Changed from 11 to 9
                print(f"DEBUG: Skipping row {row_num + 1} - insufficient cells (need at least 9)")
                continue
            
            # Let's print the first row's content to understand the structure
            if row_num == 0:
                print("DEBUG: First row cell contents:")
                for i, cell in enumerate(cells):
                    print(f"  Cell {i}: {cell.text.strip()[:50]}...")
            
            print(f"DEBUG: Processing row {row_num + 1} with {len(cells)} cells...")
            book = {}
            
            # Based on the HTML structure, let's adjust the cell mapping
            # The table seems to have merged some columns
            
            # Cell 0: Contains ID, Title, Series, Author info
            print(f"DEBUG: Extracting from cell 0...")
            first_cell = cells[0]
            
            # The first cell contains multiple pieces of information
            # Let's extract them carefully
            
            # Extract title from the first bold or link element
            title_elem = first_cell.find('b') or first_cell.find('a')
            if title_elem:
                book['title'] = title_elem.text.strip()
                print(f"DEBUG: Extracted title: {book['title']}")
            
            # Extract ID from badge
            id_badge = first_cell.find('span', {'class': 'badge-secondary'})
            if id_badge:
                id_text = id_badge.text.strip()
                if ' ' in id_text:
                    book['id'] = id_text.split()[-1]
                else:
                    book['id'] = id_text
                print(f"DEBUG: Extracted ID: {book.get('id', 'N/A')}")
            
            # Extract series if present
            series_links = first_cell.find_all('a', href=lambda x: x and 'series.php' in x)
            if series_links:
                book['series'] = '; '.join([link.text.strip() for link in series_links])
                print(f"DEBUG: Extracted series: {book.get('series', 'N/A')}")
            
            # Cell 1: Author(s)
            book['authors'] = cells[1].text.strip()
            print(f"DEBUG: Authors: {book['authors']}")
            
            # Cell 2: Publisher
            book['publisher'] = cells[2].text.strip()
            print(f"DEBUG: Publisher: {book['publisher']}")
            
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
                                print(f"DEBUG: Extracted MD5: {md5_match}")
            
            book['download_links'] = download_links
            print(f"DEBUG: Found {len(download_links)} download links")
            
            books.append(book)
            print(f"DEBUG: Successfully added book to results")
            print(f"DEBUG: Authors: {book['authors']}")
            
            # Cell 2: Publisher
            print("DEBUG: Extracting publisher from cell 2...")
            book['publisher'] = cells[2].text.strip()
            print(f"DEBUG: Publisher: {book['publisher']}")
            
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
            print(f"DEBUG: Extracting download links from cells 8-{len(cells)-1}...")
            for i in range(8, len(cells)):
                links = cells[i].find_all('a')
                for link in links:
                    if link.get('href'):
                        download_links.append({
                            'text': link.text.strip(),
                            'url': link.get('href') if link.get('href').startswith('http') else urljoin(self.base_url, link.get('href'))
                        })
            book['download_links'] = download_links
            print(f"DEBUG: Found {len(download_links)} download links")
            
            books.append(book)
            print(f"DEBUG: Successfully added book to results")
        
        print(f"\nDEBUG: Finished parsing. Total books found: {len(books)}")
        return books
    
    def save_to_csv(self, books, filename='libgen_results.csv'):
        """Save the scraped books to a CSV file"""
        if not books:
            print("No books to save")
            return
        
        # Flatten the data for CSV
        flattened_books = []
        for book in books:
            flat_book = book.copy()
            # Convert download links to a simple string
            flat_book['download_links'] = '; '.join([link['text'] for link in book.get('download_links', [])])
            flattened_books.append(flat_book)
        
        df = pd.DataFrame(flattened_books)
        df.to_csv(filename, index=False, encoding='utf-8')
        print(f"Saved {len(books)} books to {filename}")
    
    def save_to_json(self, books, filename='libgen_results.json'):
        """Save the scraped books to a JSON file"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(books, f, ensure_ascii=False, indent=2)
        print(f"Saved {len(books)} books to {filename}")


def main():
    # Example usage
    scraper = LibGenScraper()
    
    # Search for Harry Potter books
    print("Searching for 'Harry Potter' books...")
    results = scraper.search("Harry Potter", results_per_page=100)
    
    if results:
        print(f"\nFound {len(results)} books")
        
        # Display first few results
        for i, book in enumerate(results[:5]):
            print(f"\n--- Book {i+1} ---")
            print(f"ID: {book.get('id', 'N/A')}")
            print(f"Title: {book.get('title', 'N/A')}")
            print(f"Authors: {book.get('authors', 'N/A')}")
            print(f"Year: {book.get('year', 'N/A')}")
            print(f"Publisher: {book.get('publisher', 'N/A')}")
            print(f"Language: {book.get('language', 'N/A')}")
            print(f"Pages: {book.get('pages', 'N/A')}")
            print(f"Size: {book.get('size', 'N/A')}")
            print(f"Extension: {book.get('extension', 'N/A')}")
            if book.get('series'):
                print(f"Series: {book['series']}")
            
            # Display download links
            if book.get('download_links'):
                print(f"\nDownload links:")
                for j, link in enumerate(book['download_links']):
                    print(f"  Mirror {j+1} ({link['text']}): {link['url']}")
            
            # Display direct download URL if available
            if book.get('direct_download_url'):
                print(f"\nDirect download URL: {book['direct_download_url']}")
            elif book.get('md5'):
                print(f"\nMD5: {book['md5']}")
            
            # Display direct file URL if available
            if book.get('file_url'):
                print(f"File info URL: {book['file_url']}")
        
        # Save results
        scraper.save_to_csv(results, 'harry_potter_books.csv')
        scraper.save_to_json(results, 'harry_potter_books.json')
    else:
        print("No results found")


if __name__ == "__main__":
    main()
    
    
# RCW2HCXSIOAOE9R0