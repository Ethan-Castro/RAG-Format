"""
Fast web scraping module optimized for comprehensive scanning within timeout limits
"""
import logging
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
import time

logger = logging.getLogger(__name__)

def scrape_page_fast(url, headers, timeout=1.5):
    """Scrape a single page quickly"""
    try:
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract title
        title_tag = soup.find('title')
        title = title_tag.get_text().strip() if title_tag else ""
        
        # Extract links
        links = []
        for link in soup.find_all('a', href=True):
            href = link.get('href', '')
            text = link.get_text().strip()
            if href and text:
                absolute_url = urljoin(url, href)
                links.append({
                    'text': text[:200],
                    'url': absolute_url[:500],
                    'source_page': url
                })
        
        # Extract images
        images = []
        for img in soup.find_all('img'):
            src = img.get('src', '')
            if src:
                absolute_src = urljoin(url, src)
                alt_text = img.get('alt', '') or img.get('title', '') or 'Image'
                images.append({
                    'url': absolute_src[:500],
                    'title': alt_text[:200]
                })
        
        return {
            'success': True,
            'title': title,
            'links': links,
            'images': images,
            'url': url
        }
    except Exception as e:
        logger.warning(f"Error scraping {url}: {e}")
        return {
            'success': False,
            'title': '',
            'links': [],
            'images': [],
            'url': url
        }

def scrape_entire_website_fast(base_url, max_pages=30, max_depth=3, max_runtime=28):
    """
    Fast comprehensive website scraping - optimized for maximum content
    Designed to complete within 28 seconds to avoid worker timeout
    """
    logger.info(f"Starting fast comprehensive scrape for: {base_url}")
    
    start_time = time.time()
    base_domain = urlparse(base_url).netloc
    
    # Simple collections (no threading needed)
    visited_urls = set()
    all_links = []
    all_images = []
    pages_scraped = 0
    website_title = None
    
    # Queue management
    to_visit = [(base_url, 0)]  # (url, depth)
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    # Sequential processing with early exit on timeout
    while to_visit and pages_scraped < max_pages:
        # Check time limit early
        elapsed = time.time() - start_time
        if elapsed > max_runtime:
            logger.info(f"Time limit reached after {pages_scraped} pages in {elapsed:.1f}s")
            break
        
        # Get next URL to process
        current_url, depth = to_visit.pop(0)
        
        # Skip if already visited or too deep
        if current_url in visited_urls or depth > max_depth:
            continue
        
        visited_urls.add(current_url)
        
        # Scrape the page with a short timeout
        try:
            result = scrape_page_fast(current_url, headers, timeout=1.5)
            
            if result['success']:
                pages_scraped += 1
                
                # Set title from first page
                if pages_scraped == 1 and result['title']:
                    website_title = result['title']
                
                # Add links and images
                all_links.extend(result['links'])
                all_images.extend(result['images'])
                
                # Queue internal links for further exploration
                if depth < max_depth:
                    for link_data in result['links'][:20]:  # Limit to 20 links per page
                        link_url = link_data['url']
                        parsed_link = urlparse(link_url)
                        
                        # Only follow internal links
                        if parsed_link.netloc == base_domain:
                            # Avoid common non-content pages
                            avoid_patterns = [
                                '.pdf', '.jpg', '.png', '.gif', '.zip',
                                '#', 'mailto:', 'tel:', 'javascript:',
                                '/login', '/logout', '/admin'
                            ]
                            if not any(p in link_url.lower() for p in avoid_patterns):
                                if link_url not in visited_urls and len(to_visit) < 100:
                                    to_visit.append((link_url, depth + 1))
                
                logger.info(f"Scraped page {pages_scraped} of {max_pages}: {current_url[:80]}")
                
        except Exception as e:
            logger.warning(f"Error scraping {current_url}: {e}")
            continue
    
    # Remove duplicates
    unique_links = []
    seen_urls = set()
    for link in all_links:
        if len(unique_links) >= 5000:
            break
        if link['url'] not in seen_urls and link['url'].strip():
            unique_links.append(link)
            seen_urls.add(link['url'])
    
    unique_images = []
    seen_image_urls = set()
    for img in all_images:
        if len(unique_images) >= 500:
            break
        if img['url'] not in seen_image_urls and img['url'].strip():
            unique_images.append(img)
            seen_image_urls.add(img['url'])
    
    runtime = int(time.time() - start_time)
    
    # Create summary
    summary = f"Fast comprehensive scan of {base_domain}\n"
    summary += f"Pages scraped: {pages_scraped}\n"
    summary += f"Maximum depth: {max_depth}\n"
    summary += f"Unique links found: {len(unique_links)}\n"
    summary += f"Unique images found: {len(unique_images)}\n"
    summary += f"Runtime: {runtime} seconds"
    
    return {
        'url': base_url,
        'title': website_title or "Website Content",
        'content': summary,
        'links': unique_links,
        'images': unique_images,
        'pages_scraped': pages_scraped,
        'success': True,
        'error': None
    }