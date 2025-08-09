from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import black, blue
from io import BytesIO
import logging
import requests
from PIL import Image as PILImage
import tempfile
import os

logger = logging.getLogger(__name__)

def download_image(url, max_width=400, max_height=300):
    """
    Download an image from URL and return a ReportLab Image object
    """
    try:
        # Download the image with timeout
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=5, stream=True)
        response.raise_for_status()
        
        # Save to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp_file:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    tmp_file.write(chunk)
            tmp_path = tmp_file.name
        
        # Open with PIL to check dimensions and convert if needed
        try:
            pil_img = PILImage.open(tmp_path)
            
            # Convert RGBA to RGB if needed
            if pil_img.mode in ('RGBA', 'LA', 'P'):
                rgb_img = PILImage.new('RGB', pil_img.size, (255, 255, 255))
                if pil_img.mode == 'P':
                    pil_img = pil_img.convert('RGBA')
                rgb_img.paste(pil_img, mask=pil_img.split()[-1] if pil_img.mode == 'RGBA' else None)
                pil_img = rgb_img
            
            # Resize if too large
            width, height = pil_img.size
            if width > max_width or height > max_height:
                ratio = min(max_width/width, max_height/height)
                new_width = int(width * ratio)
                new_height = int(height * ratio)
                pil_img = pil_img.resize((new_width, new_height), PILImage.Resampling.LANCZOS)
            
            # Save the processed image
            processed_path = tmp_path.replace('.jpg', '_processed.jpg')
            pil_img.save(processed_path, 'JPEG', quality=85)
            
            # Create ReportLab Image
            img = Image(processed_path)
            img.drawHeight = min(pil_img.height, max_height)
            img.drawWidth = min(pil_img.width, max_width)
            
            # Clean up original temp file
            os.unlink(tmp_path)
            
            return img, processed_path
            
        except Exception as e:
            logger.warning(f"Error processing image: {e}")
            os.unlink(tmp_path)
            return None, None
            
    except Exception as e:
        logger.warning(f"Error downloading image from {url}: {e}")
        return None, None

def generate_pdf(scraped_data):
    """
    Generate a PDF from scraped website data
    Returns a BytesIO object containing the PDF
    """
    try:
        # Create a BytesIO buffer to store the PDF
        buffer = BytesIO()
        
        # Create the PDF document
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18
        )
        
        # Get styles
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            textColor=black
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            spaceBefore=20,
            spaceAfter=12,
            textColor=black
        )
        
        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontSize=11,
            spaceAfter=12,
            leading=14
        )
        
        link_style = ParagraphStyle(
            'LinkStyle',
            parent=styles['Normal'],
            fontSize=10,
            leftIndent=20,
            spaceAfter=6,
            textColor=blue
        )
        
        # Build the story (content) for the PDF
        story = []
        
        # Add title
        if scraped_data.get('title'):
            story.append(Paragraph(f"Links from: {scraped_data['title']}", title_style))
        else:
            story.append(Paragraph("Website Links", title_style))
        
        # Add URL
        story.append(Paragraph(f"<b>Source URL:</b> {scraped_data['url']}", normal_style))
        story.append(Spacer(1, 20))
        
        # Add images section if available
        if scraped_data.get('images'):
            images = scraped_data['images']
            total_images = len(images)
            story.append(Paragraph(f"Images Found ({total_images})", heading_style))
            story.append(Spacer(1, 12))
            
            # Track temporary files to clean up
            temp_files = []
            
            # Process images (limit to first 20 to prevent memory issues)
            for i, img_data in enumerate(images[:20]):
                try:
                    img_url = img_data.get('url', '')
                    img_title = img_data.get('title', 'Untitled Image')
                    
                    # Add image title
                    story.append(Paragraph(f"<b>{img_title}</b>", normal_style))
                    story.append(Paragraph(f"<font color='blue'>{img_url[:200]}</font>", normal_style))
                    
                    # Try to download and display the image
                    img_obj, temp_path = download_image(img_url)
                    if img_obj:
                        story.append(img_obj)
                        if temp_path:
                            temp_files.append(temp_path)
                    else:
                        story.append(Paragraph("<i>[Image could not be loaded]</i>", normal_style))
                    
                    story.append(Spacer(1, 12))
                    
                    # Add page break every 5 images
                    if (i + 1) % 5 == 0 and i + 1 < min(20, total_images):
                        story.append(PageBreak())
                        story.append(Paragraph(f"Images (continued - {i+1}/{min(20, total_images)})", heading_style))
                        
                except Exception as e:
                    logger.warning(f"Error processing image {i}: {e}")
                    continue
            
            # If there are more than 20 images, add a note
            if total_images > 20:
                story.append(Paragraph(f"<i>Note: Showing first 20 of {total_images} images found</i>", normal_style))
                story.append(Spacer(1, 12))
            
            story.append(PageBreak())
        
        # Add links section - format exactly like the user's example
        if scraped_data.get('links'):
            links = scraped_data['links']
            total_links = len(links)
            story.append(Paragraph(f"Links Found ({total_links})", heading_style))
            
            # Process links in smaller chunks to avoid memory issues
            for i, link in enumerate(links):
                try:
                    link_text = str(link.get('text', '')).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                    link_url = str(link.get('url', '')).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                    
                    # Limit text length to prevent overflow
                    if len(link_text) > 100:
                        link_text = link_text[:97] + "..."
                    if len(link_url) > 200:
                        link_url = link_url[:197] + "..."
                    
                    # Format exactly like user's example: text on one line, URL on next line
                    story.append(Paragraph(f"<b>{link_text}</b>", normal_style))
                    story.append(Paragraph(f"<font color='blue'>{link_url}</font>", normal_style))
                    story.append(Spacer(1, 6))  # Small space between links
                    
                    # Add page break every 50 links to prevent memory issues
                    if (i + 1) % 50 == 0 and i + 1 < total_links:
                        story.append(PageBreak())
                        story.append(Paragraph(f"Links Found (continued - {i+1}/{total_links})", heading_style))
                        
                except Exception as e:
                    logger.warning(f"Error processing link {i}: {e}")
                    continue
        
        # Build the PDF
        doc.build(story)
        
        # Clean up temporary image files if any
        if 'temp_files' in locals():
            for temp_file in temp_files:
                try:
                    if os.path.exists(temp_file):
                        os.unlink(temp_file)
                except Exception as e:
                    logger.warning(f"Could not delete temp file {temp_file}: {e}")
        
        # Get the PDF data
        buffer.seek(0)
        return buffer
        
    except Exception as e:
        logger.error(f"Error generating PDF: {e}")
        raise Exception(f"Failed to generate PDF: {str(e)}")

def create_error_pdf(error_message, url):
    """
    Create a PDF with error information
    """
    try:
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        styles = getSampleStyleSheet()
        
        story = []
        story.append(Paragraph("Website Scraping Error", styles['Title']))
        story.append(Spacer(1, 12))
        story.append(Paragraph(f"<b>URL:</b> {url}", styles['Normal']))
        story.append(Spacer(1, 12))
        story.append(Paragraph(f"<b>Error:</b> {error_message}", styles['Normal']))
        
        doc.build(story)
        buffer.seek(0)
        return buffer
        
    except Exception as e:
        logger.error(f"Error creating error PDF: {e}")
        return None
