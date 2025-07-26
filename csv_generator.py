import csv
import io
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def generate_csv(scraped_data):
    """
    Generate CSV file from scraped website data
    Returns a BytesIO buffer containing the CSV data
    """
    try:
        # Create a string buffer
        output = io.StringIO()
        
        # Create CSV writer
        writer = csv.writer(output)
        
        # Write header information
        writer.writerow(['Website Information'])
        writer.writerow(['URL', scraped_data.get('url', 'N/A')])
        writer.writerow(['Title', scraped_data.get('title', 'N/A')])
        writer.writerow(['Scraped Date', datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
        writer.writerow(['Total Links Found', len(scraped_data.get('links', []))])
        writer.writerow([])  # Empty row for separation
        
        # Write links header
        writer.writerow(['Links Found on Website'])
        writer.writerow(['Link Text', 'URL', 'Domain'])
        
        # Write all links
        links = scraped_data.get('links', [])
        for link in links:
            try:
                from urllib.parse import urlparse
                parsed_url = urlparse(link.get('url', ''))
                domain = parsed_url.netloc
                
                writer.writerow([
                    link.get('text', '').strip(),
                    link.get('url', ''),
                    domain
                ])
            except Exception as e:
                logger.warning(f"Error processing link for CSV: {e}")
                writer.writerow([
                    link.get('text', '').strip(),
                    link.get('url', ''),
                    'Unknown'
                ])
        
        # Convert to bytes
        csv_content = output.getvalue()
        output.close()
        
        # Create BytesIO buffer
        buffer = io.BytesIO()
        buffer.write(csv_content.encode('utf-8-sig'))  # UTF-8 with BOM for Excel compatibility
        buffer.seek(0)
        
        return buffer
        
    except Exception as e:
        logger.error(f"Error generating CSV: {e}")
        return None

def create_error_csv(error_message, url):
    """
    Create an error CSV file when scraping fails
    """
    try:
        output = io.StringIO()
        writer = csv.writer(output)
        
        writer.writerow(['Scraping Error Report'])
        writer.writerow(['URL', url])
        writer.writerow(['Error', error_message])
        writer.writerow(['Date', datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
        
        csv_content = output.getvalue()
        output.close()
        
        buffer = io.BytesIO()
        buffer.write(csv_content.encode('utf-8-sig'))
        buffer.seek(0)
        
        return buffer
        
    except Exception as e:
        logger.error(f"Error creating error CSV: {e}")
        return None