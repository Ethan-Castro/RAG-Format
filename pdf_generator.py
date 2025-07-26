from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import black, blue
from io import BytesIO
import logging

logger = logging.getLogger(__name__)

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
