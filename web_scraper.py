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

def extract_images_from_page(soup, base_url):
    """
    Extract all images from a page with their URLs and alt text
    """
    images = []
    img_tags = soup.find_all('img')
    
    # Limit to first 100 images to prevent memory issues
    for img in img_tags[:100]:
        try:
            src = img.get('src', '')
            if src:
                # Make URL absolute
                absolute_url = urljoin(base_url, src)
                
                # Get alt text or title as the image name
                alt_text = img.get('alt', '')
                title = img.get('title', '')
                image_name = alt_text or title or 'Untitled Image'
                
                images.append({
                    'url': absolute_url[:500],  # Limit URL length
                    'title': image_name[:200],  # Limit title length
                    'alt': alt_text[:200]
                })
        except Exception as e:
            logger.warning(f"Error extracting image: {e}")
            continue
    
    return images

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
        
        # Extract images from the page
        images = extract_images_from_page(soup, url)
        
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
            'images': images,  # Return extracted images
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
            'images': [],
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
            'images': [],
            'success': False,
            'error': f"An unexpected error occurred: {str(e)}"
        }

def scrape_entire_website(base_url, max_pages=50, max_depth=3):
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
        
        # Set time limit for entire operation (4 minutes max for comprehensive scanning)
        start_time = time.time()
        max_runtime = 240  # seconds
        
        # Parse the base URL to determine the domain
        base_domain = urlparse(base_url).netloc
        
        # Keep track of visited URLs and collected links
        visited_urls = set()
        all_links = []
        all_images = []  # Collect images from all pages
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
                # Check time limit early to avoid worker timeouts
                if (time.time() - start_time) > (max_runtime - 30):
                    logger.info(f"Approaching time limit, stopping at {pages_scraped} pages")
                    break
                
                logger.info(f"Scraping page {pages_scraped + 1} (depth {depth}): {current_url}")
                
                # Get the page with shorter timeout and better error handling
                try:
                    response = requests.get(current_url, headers=headers, timeout=5)
                    response.raise_for_status()
                except (requests.Timeout, requests.ConnectionError) as e:
                    logger.warning(f"Network timeout/error for {current_url}: {e}")
                    continue
                except requests.RequestException as e:
                    logger.warning(f"Request error for {current_url}: {e}")
                    continue
                
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Get website title from first page
                if pages_scraped == 0:
                    title_tag = soup.find('title')
                    website_title = title_tag.get_text().strip() if title_tag else "Website Content"
                
                # Extract images from this page
                page_images = extract_images_from_page(soup, current_url)
                all_images.extend(page_images)
                
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
                time.sleep(0.05)  # Reduced delay for faster scanning
                
            except Exception as e:
                logger.warning(f"Error scraping page {current_url}: {e}")
                continue
        
        # Remove duplicate links based on URL
        unique_links = []
        seen_urls = set()
        for link in all_links:
            if len(unique_links) >= 10000:  # Increased limit for comprehensive scanning
                break
            if link['url'] not in seen_urls and link['url'].strip():
                unique_links.append(link)
                seen_urls.add(link['url'])
        
        # Remove duplicate images based on URL
        unique_images = []
        seen_image_urls = set()
        for img in all_images:
            if len(unique_images) >= 1000:  # Increased limit for more comprehensive image collection
                break
            if img['url'] not in seen_image_urls and img['url'].strip():
                unique_images.append(img)
                seen_image_urls.add(img['url'])
        
        # Create comprehensive content summary
        comprehensive_content = f"Comprehensive scan of {base_domain}\n"
        comprehensive_content += f"Pages scraped: {pages_scraped}\n"
        comprehensive_content += f"Maximum depth reached: {max_depth}\n"
        comprehensive_content += f"Total links collected from all pages: {len(all_links)}\n"
        comprehensive_content += f"Total unique links found: {len(unique_links)}\n"
        comprehensive_content += f"Total images found: {len(unique_images)}\n"
        comprehensive_content += f"Base URL: {base_url}\n"
        comprehensive_content += f"Runtime: {int(time.time() - start_time)} seconds"
        
        return {
            'url': base_url,
            'title': website_title,
            'content': comprehensive_content,
            'links': unique_links,
            'images': unique_images,  # Return collected images
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
            'images': [],
            'pages_scraped': 0,
            'success': False,
            'error': f"Comprehensive scraping failed: {str(e)}"
        }
