"""
Fast web scraping module optimized for comprehensive scanning within timeout limits
"""
import logging
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

logger = logging.getLogger(__name__)

def scrape_page_fast(url, headers, timeout=2):
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

def scrape_entire_website_fast(base_url, max_pages=15, max_depth=2, max_runtime=18):
    """
    Fast comprehensive website scraping with parallel requests
    Designed to complete within 20 seconds to avoid timeouts
    """
    logger.info(f"Starting fast comprehensive scrape for: {base_url}")
    
    start_time = time.time()
    base_domain = urlparse(base_url).netloc
    
    # Threading-safe collections
    visited_urls = set()
    all_links = []
    all_images = []
    pages_scraped = 0
    website_title = None
    lock = threading.Lock()
    
    # Queue management
    to_visit = [(base_url, 0)]  # (url, depth)
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    # Process pages in batches with threading
    with ThreadPoolExecutor(max_workers=5) as executor:
        while to_visit and pages_scraped < max_pages:
            # Check time limit
            if (time.time() - start_time) > max_runtime:
                logger.info(f"Time limit reached after {pages_scraped} pages")
                break
            
            # Get batch of URLs to process (up to 5 at a time)
            batch = []
            batch_size = min(5, len(to_visit), max_pages - pages_scraped)
            
            for _ in range(batch_size):
                if not to_visit:
                    break
                url, depth = to_visit.pop(0)
                
                # Skip if already visited or too deep
                with lock:
                    if url in visited_urls or depth > max_depth:
                        continue
                    visited_urls.add(url)
                
                batch.append((url, depth))
            
            if not batch:
                continue
            
            # Submit batch for parallel processing
            futures = {
                executor.submit(scrape_page_fast, url, headers): (url, depth)
                for url, depth in batch
            }
            
            # Process results as they complete
            for future in as_completed(futures, timeout=5):
                url, depth = futures[future]
                
                try:
                    result = future.result(timeout=3)
                    
                    if result['success']:
                        with lock:
                            pages_scraped += 1
                            
                            # Set title from first page
                            if pages_scraped == 1 and result['title']:
                                website_title = result['title']
                            
                            # Add links
                            all_links.extend(result['links'])
                            
                            # Add images
                            all_images.extend(result['images'])
                            
                            # Queue internal links for further exploration
                            if depth < max_depth:
                                for link_data in result['links']:
                                    link_url = link_data['url']
                                    parsed_link = urlparse(link_url)
                                    
                                    # Only follow internal links
                                    if parsed_link.netloc == base_domain:
                                        # Avoid common non-content pages
                                        avoid_patterns = [
                                            '.pdf', '.jpg', '.png', '.gif', '.zip',
                                            '#', 'mailto:', 'tel:', 'javascript:'
                                        ]
                                        if not any(p in link_url.lower() for p in avoid_patterns):
                                            with lock:
                                                if link_url not in visited_urls:
                                                    to_visit.append((link_url, depth + 1))
                        
                        logger.info(f"Scraped page {pages_scraped}: {url}")
                        
                except Exception as e:
                    logger.warning(f"Error processing {url}: {e}")
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