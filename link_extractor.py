import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import logging

logger = logging.getLogger(__name__)

def extract_links_from_website(url):
    """
    Extract links from website exactly like the provided code
    Returns a list of dictionaries with 'text' and 'url' keys
    """
    try:
        # Add headers to avoid being blocked
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract links exactly like your code
        links = []
        all_links = soup.find_all('a', href=True)
        
        for link in all_links:
            try:
                text = link.string or link.get_text()
                if text:
                    text = text.strip()
                
                # Get href using dict-like access
                href_attrs = dict(link.attrs) if hasattr(link, 'attrs') else {}
                link_url = href_attrs.get('href', '')
                
                if text and link_url:
                    # Make relative URLs absolute
                    absolute_url = urljoin(url, str(link_url))
                    links.append({
                        'text': text,
                        'url': absolute_url
                    })
            except:
                # Skip any problematic links
                continue
        
        return links
        
    except Exception as e:
        logger.error(f"Error extracting links from {url}: {e}")
        return []