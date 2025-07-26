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

def scrape_entire_website(base_url, max_pages=30, max_depth=3):
    """
    Comprehensively scrape an entire website by following internal links
    
    Args:
        base_url: The starting URL
        max_pages: Maximum number of pages to scrape (to prevent infinite loops)
        max_depth: Maximum depth to follow links
    
    Returns:
        Dictionary with all links found across the entire website
    """
    if not validate_url(base_url):
        return {
            'url': base_url,
            'title': None,
            'content': None,
            'links': [],
            'pages_scraped': 0,
            'success': False,
            'error': "Invalid URL format"
        }
    
    try:
        from urllib.parse import urlparse, urljoin
        import time
        
        # Set time limit for entire operation (2 minutes max)
        start_time = time.time()
        max_runtime = 120  # seconds
        
        # Parse the base URL to determine the domain
        base_domain = urlparse(base_url).netloc
        
        # Keep track of visited URLs and collected links
        visited_urls = set()
        all_links = []
        pages_scraped = 0
        queue = [(base_url, 0)]  # (url, depth)
        website_title = None
        
        # Headers to avoid being blocked
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        while queue and pages_scraped < max_pages and (time.time() - start_time) < max_runtime:
            current_url, depth = queue.pop(0)
            
            # Skip if already visited or too deep
            if current_url in visited_urls or depth > max_depth:
                continue
                
            visited_urls.add(current_url)
            
            try:
                logger.info(f"Scraping page {pages_scraped + 1} (depth {depth}): {current_url}")
                
                # Get the page
                response = requests.get(current_url, headers=headers, timeout=10)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Get website title from first page
                if pages_scraped == 0:
                    title_tag = soup.find('title')
                    website_title = title_tag.get_text().strip() if title_tag else "Website Content"
                
                # Extract all links from this page
                page_links = soup.find_all('a', href=True)
                
                for link in page_links:
                    try:
                        text = link.get_text().strip()
                        href = link.get('href', '')
                        
                        if text and href:
                            absolute_url = urljoin(current_url, href)
                            parsed_link = urlparse(absolute_url)
                            
                            # Add to all_links collection
                            all_links.append({
                                'text': text[:200],  # Limit text length
                                'url': absolute_url[:500],  # Limit URL length
                                'source_page': current_url
                            })
                            
                            # Add internal links to queue for further exploration
                            if (parsed_link.netloc == base_domain and 
                                absolute_url not in visited_urls and
                                depth < max_depth):
                                
                                # Avoid common non-content pages
                                avoid_patterns = [
                                    '/logout', '/login', '/register', '/admin',
                                    '.pdf', '.jpg', '.jpeg', '.png', '.gif',
                                    '.zip', '.doc', '.docx', '.xls', '.xlsx',
                                    '#', 'mailto:', 'tel:', 'javascript:'
                                ]
                                
                                if not any(pattern in absolute_url.lower() for pattern in avoid_patterns):
                                    queue.append((absolute_url, depth + 1))
                                    
                    except Exception as e:
                        logger.warning(f"Error processing link: {e}")
                        continue
                
                pages_scraped += 1
                
                # Add small delay to be respectful to the server
                import time
                time.sleep(0.1)
                
            except Exception as e:
                logger.warning(f"Error scraping page {current_url}: {e}")
                continue
        
        # Remove duplicate links based on URL
        unique_links = []
        seen_urls = set()
        for link in all_links:
            if len(unique_links) >= 2000:  # Limit total links to prevent memory issues
                break
            if link['url'] not in seen_urls and link['url'].strip():
                unique_links.append(link)
                seen_urls.add(link['url'])
        
        # Create comprehensive content summary
        comprehensive_content = f"Comprehensive scan of {base_domain}\n"
        comprehensive_content += f"Pages scraped: {pages_scraped}\n"
        comprehensive_content += f"Total unique links found: {len(unique_links)}\n"
        comprehensive_content += f"Base URL: {base_url}"
        
        return {
            'url': base_url,
            'title': website_title,
            'content': comprehensive_content,
            'links': unique_links,
            'pages_scraped': pages_scraped,
            'success': True,
            'error': None
        }
        
    except Exception as e:
        logger.error(f"Unexpected error in comprehensive scraping: {e}")
        return {
            'url': base_url,
            'title': None,
            'content': None,
            'links': [],
            'pages_scraped': 0,
            'success': False,
            'error': f"Comprehensive scraping failed: {str(e)}"
        }
