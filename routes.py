from flask import render_template, request, redirect, url_for, flash, send_file, abort
from app import app, db
from models import ScrapeHistory
from web_scraper import scrape_website_content
from pdf_generator import generate_pdf, create_error_pdf
import logging
import json
from datetime import datetime

logger = logging.getLogger(__name__)

@app.route('/')
def index():
    """Home page with URL input form"""
    return render_template('index.html')

@app.route('/scrape', methods=['GET', 'POST'])
def scrape():
    """Handle the scraping request"""
    if request.method == 'GET':
        # If accessed via GET, redirect to home
        return redirect(url_for('index'))
        
    url = request.form.get('url', '').strip()
    
    if not url:
        flash('Please enter a valid URL', 'error')
        return redirect(url_for('index'))
    
    # Add http:// if no protocol is specified
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    try:
        # Scrape the website
        scraped_data = scrape_website_content(url)
        
        # Save to database
        scrape_record = ScrapeHistory(
            url=url,
            title=scraped_data.get('title'),
            success=scraped_data['success'],
            error_message=scraped_data.get('error')
        )
        db.session.add(scrape_record)
        db.session.commit()
        
        if scraped_data['success']:
            return render_template('result.html', data=scraped_data)
        else:
            flash(f"Failed to scrape website: {scraped_data['error']}", 'error')
            return redirect(url_for('index'))
            
    except Exception as e:
        logger.error(f"Error in scrape route: {e}")
        flash(f"An unexpected error occurred: {str(e)}", 'error')
        return redirect(url_for('index'))

@app.route('/download_pdf', methods=['POST'])
def download_pdf():
    """Generate and download PDF of scraped content"""
    try:
        # Get the URL and re-scrape to ensure we have fresh link data
        url = request.form.get('url')
        
        if not url:
            abort(400, "Missing required data for PDF generation")
        
        # Re-scrape the website to get fresh data with links
        scraped_data = scrape_website_content(url)
        
        if not scraped_data['success']:
            # If scraping fails, try with minimal data
            scraped_data = {
                'url': url,
                'title': request.form.get('title') or 'Website Content',
                'content': request.form.get('content') or 'No content available',
                'links': []
            }
        
        # Generate PDF
        pdf_buffer = generate_pdf(scraped_data)
        
        # Create a safe filename
        safe_title = "".join(c for c in (scraped_data.get('title') or "website_links") if c.isalnum() or c in (' ', '-', '_')).rstrip()
        filename = f"{safe_title[:50]}.pdf"
        
        return send_file(
            pdf_buffer,
            as_attachment=True,
            download_name=filename,
            mimetype='application/pdf'
        )
        
    except Exception as e:
        logger.error(f"Error generating PDF: {e}")
        
        # Try to create an error PDF
        error_pdf = create_error_pdf(str(e), request.form.get('url') or "Unknown URL")
        if error_pdf:
            return send_file(
                error_pdf,
                as_attachment=True,
                download_name="error_report.pdf",
                mimetype='application/pdf'
            )
        else:
            flash("Failed to generate PDF. Please try again.", 'error')
            return redirect(url_for('index'))

@app.route('/history')
def history():
    """Show scraping history"""
    try:
        records = ScrapeHistory.query.order_by(ScrapeHistory.scrape_date.desc()).limit(50).all()
        return render_template('history.html', records=records)
    except Exception as e:
        logger.error(f"Error fetching history: {e}")
        flash("Failed to load history", 'error')
        return redirect(url_for('index'))

@app.errorhandler(404)
def not_found_error(error):
    return render_template('error.html', error="Page not found"), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('error.html', error="Internal server error"), 500
