import requests
from bs4 import BeautifulSoup
import trafilatura
from urllib.parse import urljoin, urlparse
import logging
from link_extractor import extract_links_from_website

logger = logging.getLogger(__name__)

def validate_url(url):
    """Validate if the URL is properly formatted"""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False

def get_website_text_content(url: str) -> str:
    """
    Extract main text content using trafilatura for better readability
    """
    try:
        downloaded = trafilatura.fetch_url(url)
        if downloaded:
            # Limit the size of content we process to prevent memory issues
            if len(downloaded) > 500000:  # 500KB limit to prevent memory crashes
                downloaded = downloaded[:500000]
            
            text = trafilatura.extract(downloaded)
            return text or ""
        return ""
    except Exception as e:
        logger.error(f"Error extracting text content from {url}: {e}")
        return ""

def scrape_website_content(url):
    """
    Scrape website content including title, text, and links
    Returns a dictionary with structured data
    """
    if not validate_url(url):
        raise ValueError("Invalid URL format")
    
    try:
        # Add headers to avoid being blocked by some websites
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract title
        title = soup.find('title')
        title_text = title.get_text().strip() if title else "No Title Found"
        
        # Extract main content using trafilatura
        main_content = get_website_text_content(url)
        
        # Extract all links exactly like your code (limit to prevent memory issues)
        links = []
        all_links = soup.find_all('a', href=True)
        
        # Limit processing to first 1000 links to prevent memory crashes
        for i, link in enumerate(all_links[:1000]):
            try:
                text = link.get_text().strip()
                href = link.get('href', '')
                if text and href:
                    absolute_url = urljoin(url, href)
                    links.append({
                        'text': text[:200],  # Limit text length
                        'url': absolute_url[:500]  # Limit URL length
                    })
            except:
                continue
        
        # Remove duplicate links based on URL (limit to 500 unique links)
        unique_links = []
        seen_urls = set()
        for link in links:
            if len(unique_links) >= 500:  # Limit to prevent memory issues
                break
            if link['url'] not in seen_urls and link['url'].strip():
                unique_links.append(link)
                seen_urls.add(link['url'])
        
        return {
            'url': url,
            'title': title_text,
            'content': main_content,
            'links': unique_links,  # Return all unique links
            'success': True,
            'error': None
        }
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error for {url}: {e}")
        return {
            'url': url,
            'title': None,
            'content': None,
            'links': [],
            'success': False,
            'error': f"Failed to fetch the website: {str(e)}"
        }
    except Exception as e:
        logger.error(f"Unexpected error scraping {url}: {e}")
        return {
            'url': url,
            'title': None,
            'content': None,
            'links': [],
            'success': False,
            'error': f"An unexpected error occurred: {str(e)}"
        }
