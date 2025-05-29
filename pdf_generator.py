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
            story.append(Paragraph(f"Website Content: {scraped_data['title']}", title_style))
        else:
            story.append(Paragraph("Website Content", title_style))
        
        # Add URL
        story.append(Paragraph(f"<b>Source URL:</b> {scraped_data['url']}", normal_style))
        story.append(Spacer(1, 12))
        
        # Add main content
        if scraped_data.get('content'):
            story.append(Paragraph("Main Content", heading_style))
            
            # Split content into paragraphs and clean it
            content_paragraphs = scraped_data['content'].split('\n')
            for para in content_paragraphs:
                para = para.strip()
                if para:  # Only add non-empty paragraphs
                    # Escape HTML characters and handle encoding
                    para = para.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                    story.append(Paragraph(para, normal_style))
            
            story.append(Spacer(1, 20))
        
        # Add links section
        if scraped_data.get('links'):
            story.append(Paragraph("Links Found on the Page", heading_style))
            
            for i, link in enumerate(scraped_data['links'][:50], 1):  # Limit to 50 links for PDF
                link_text = link['text'].replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                link_url = link['url'].replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                
                # Create a formatted link entry
                link_entry = f"{i}. <b>{link_text}</b><br/><font color='blue'>{link_url}</font>"
                story.append(Paragraph(link_entry, link_style))
        
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
