import requests
from bs4 import BeautifulSoup
import trafilatura
from urllib.parse import urljoin, urlparse
import logging

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
        
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract title
        title = soup.find('title')
        title_text = title.get_text().strip() if title else "No Title Found"
        
        # Extract main content using trafilatura
        main_content = get_website_text_content(url)
        
        # Extract ALL links including hyperlinks - simplified approach
        links = []
        for link in soup.find_all('a', href=True):
            try:
                # Get text and href safely
                link_text = ""
                link_url = ""
                
                if hasattr(link, 'get_text'):
                    link_text = link.get_text().strip()
                
                if hasattr(link, 'attrs') and 'href' in link.attrs:
                    link_url = str(link.attrs['href']).strip()
                
                # Skip empty or meaningless URLs
                if not link_url or link_url in ['#', '', 'javascript:void(0)', 'javascript:;']:
                    continue
                
                # Make relative URLs absolute
                absolute_url = urljoin(url, link_url)
                
                # If no text, use a cleaned version of the URL
                display_text = link_text if link_text else absolute_url.split('/')[-1] or absolute_url
                
                links.append({
                    'text': display_text,
                    'url': absolute_url
                })
            except Exception as e:
                # Skip problematic links but continue processing
                logger.debug(f"Skipping link due to error: {e}")
                continue
        
        # Remove duplicate links based on URL
        unique_links = []
        seen_urls = set()
        for link in links:
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
