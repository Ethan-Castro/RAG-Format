from flask import render_template, request, redirect, url_for, flash, send_file, abort
from app import app, db
from models import ScrapeHistory
from web_scraper import scrape_website_content, scrape_entire_website
from pdf_generator import generate_pdf, create_error_pdf
from csv_generator import generate_csv, create_error_csv
import logging
import json
from datetime import datetime
import os
from werkzeug.utils import secure_filename
import uuid

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
        scrape_record = ScrapeHistory()
        scrape_record.url = url
        scrape_record.title = scraped_data.get('title')
        scrape_record.success = scraped_data['success']
        scrape_record.error_message = scraped_data.get('error')
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
        is_comprehensive = request.form.get('is_comprehensive') == 'true'
        
        if not url:
            abort(400, "Missing required data for PDF generation")
        
        # Choose scraping method based on scan type
        if is_comprehensive:
            logger.info(f"Generating PDF for comprehensive scan of {url}")
            scraped_data = scrape_entire_website(url)
            logger.info(f"Comprehensive scan complete: {len(scraped_data.get('links', []))} links found")
        else:
            scraped_data = scrape_website_content(url)
        
        if not scraped_data['success']:
            # If scraping fails, try with minimal data
            scraped_data = {
                'url': url,
                'title': request.form.get('title') or 'Website Content',
                'content': request.form.get('content') or 'No content available',
                'links': [],
                'images': []
            }
        
        # Add images data if available from form
        if 'images_data' in request.form:
            try:
                import json
                scraped_data['images'] = json.loads(request.form.get('images_data', '[]'))
            except:
                pass
        
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

@app.route('/download_csv', methods=['POST'])
def download_csv():
    """Generate and download CSV of scraped content"""
    try:
        # Get the URL and re-scrape to ensure we have fresh link data
        url = request.form.get('url')
        is_comprehensive = request.form.get('is_comprehensive') == 'true'
        
        if not url:
            abort(400, "Missing required data for CSV generation")
        
        # Choose scraping method based on scan type
        if is_comprehensive:
            logger.info(f"Generating CSV for comprehensive scan of {url}")
            scraped_data = scrape_entire_website(url)
            logger.info(f"Comprehensive scan complete: {len(scraped_data.get('links', []))} links found")
        else:
            scraped_data = scrape_website_content(url)
        
        if not scraped_data['success']:
            # If scraping fails, try with minimal data
            scraped_data = {
                'url': url,
                'title': request.form.get('title') or 'Website Content',
                'content': request.form.get('content') or 'No content available',
                'links': [],
                'images': []
            }
        
        # Add images data if available from form
        if 'images_data' in request.form:
            try:
                import json
                scraped_data['images'] = json.loads(request.form.get('images_data', '[]'))
            except:
                pass
        
        # Generate CSV
        csv_buffer = generate_csv(scraped_data)
        
        if not csv_buffer:
            raise Exception("Failed to generate CSV content")
        
        # Create a safe filename
        safe_title = "".join(c for c in (scraped_data.get('title') or "website_links") if c.isalnum() or c in (' ', '-', '_')).rstrip()
        filename = f"{safe_title[:50]}.csv"
        
        return send_file(
            csv_buffer,
            as_attachment=True,
            download_name=filename,
            mimetype='text/csv'
        )
        
    except Exception as e:
        logger.error(f"Error generating CSV: {e}")
        
        # Try to create an error CSV
        error_csv = create_error_csv(str(e), request.form.get('url') or "Unknown URL")
        if error_csv:
            return send_file(
                error_csv,
                as_attachment=True,
                download_name="error_report.csv",
                mimetype='text/csv'
            )
        else:
            flash("Failed to generate CSV. Please try again.", 'error')
            return redirect(url_for('index'))

@app.route('/upload-images')
def upload_images_page():
    """Display the image upload page"""
    return render_template('upload_images.html')

@app.route('/upload-images', methods=['POST'])
def upload_images():
    """Handle image uploads and generate PDF"""
    try:
        import requests
        from bs4 import BeautifulSoup
        
        # Check if files were uploaded
        if 'images' not in request.files:
            flash('No images selected', 'error')
            return redirect(url_for('upload_images_page'))
        
        files = request.files.getlist('images')
        
        if not files or all(f.filename == '' for f in files):
            flash('No images selected', 'error')
            return redirect(url_for('upload_images_page'))
        
        # Process uploaded images
        image_data = []
        allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
        
        for file in files:
            if file and file.filename:
                # Get file extension
                filename = secure_filename(file.filename)
                file_ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
                
                if file_ext in allowed_extensions:
                    try:
                        # Read file data
                        file.seek(0)
                        file_content = file.read()
                        
                        # Upload to PostImages.org
                        upload_url = "https://postimages.org/json/rr"
                        
                        files_data = {
                            'file': (filename, file_content, f'image/{file_ext}')
                        }
                        
                        # PostImages parameters
                        data = {
                            'numfiles': '1',
                            'optsize': '0',  # Don't resize
                            'expire': '0',   # Never expire
                            'upload': 'Upload'
                        }
                        
                        response = requests.post(upload_url, files=files_data, data=data, timeout=15)
                        
                        if response.status_code == 200:
                            result = response.json()
                            if result.get('status') == 'OK' and result.get('url'):
                                # Get the direct image URL
                                hosted_url = result.get('url')
                                
                                # Get original filename without extension for title
                                title = os.path.splitext(filename)[0]
                                
                                image_data.append({
                                    'title': title,
                                    'url': hosted_url,
                                    'alt': title,
                                    'filename': filename
                                })
                                logger.info(f"Successfully uploaded {filename} to PostImages: {hosted_url}")
                            else:
                                logger.warning(f"Failed to upload {filename} to PostImages: {result}")
                        else:
                            logger.warning(f"PostImages upload failed for {filename}: {response.status_code}")
                            
                    except Exception as e:
                        logger.error(f"Error uploading {filename}: {e}")
                        continue
        
        if not image_data:
            flash('No valid images were uploaded', 'error')
            return redirect(url_for('upload_images_page'))
        
        # Create data structure for PDF generation
        scraped_data = {
            'url': 'Uploaded Images',
            'title': f'Image Collection - {len(image_data)} images',
            'content': f'This PDF contains {len(image_data)} uploaded images with their hosted URLs.',
            'links': [],
            'images': image_data,
            'success': True
        }
        
        # Generate PDF
        pdf_buffer = generate_pdf(scraped_data)
        
        # Create filename for download
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"uploaded_images_{timestamp}.pdf"
        
        return send_file(
            pdf_buffer,
            as_attachment=True,
            download_name=filename,
            mimetype='application/pdf'
        )
        
    except Exception as e:
        logger.error(f"Error processing uploaded images: {e}")
        flash(f"Error processing images: {str(e)}", 'error')
        return redirect(url_for('upload_images_page'))

@app.route('/scrape_entire', methods=['POST'])
def scrape_entire():
    """Handle comprehensive website scraping (all pages)"""
    url = request.form.get('url', '').strip()
    
    if not url:
        flash('Please enter a valid URL', 'error')
        return redirect(url_for('index'))
    
    # Add http:// if no protocol is specified
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    try:
        # Scrape the entire website
        scraped_data = scrape_entire_website(url)
        
        # Save to database
        scrape_record = ScrapeHistory()
        scrape_record.url = url
        scrape_record.title = scraped_data.get('title')
        scrape_record.success = scraped_data['success']
        scrape_record.error_message = scraped_data.get('error')
        db.session.add(scrape_record)
        db.session.commit()
        
        if scraped_data['success']:
            # Mark this as a comprehensive scrape for the template
            scraped_data['is_comprehensive'] = True
            return render_template('result.html', data=scraped_data)
        else:
            flash(f"Failed to scrape website comprehensively: {scraped_data['error']}", 'error')
            return redirect(url_for('index'))
            
    except Exception as e:
        logger.error(f"Error in comprehensive scrape route: {e}")
        flash(f"An unexpected error occurred: {str(e)}", 'error')
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
