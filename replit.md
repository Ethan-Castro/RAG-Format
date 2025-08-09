# RAG Format

## Overview

This is a Flask-based web application that transforms web content into AI-ready format for RAG (Retrieval-Augmented Generation) systems. The application extracts links, content, and images from websites and generates structured PDF/CSV documents optimized for AI applications and LLM consumption.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Backend Architecture
- **Framework**: Flask (Python web framework)
- **Database**: SQLAlchemy with configurable database backend (defaults to SQLite)
- **Web Scraping**: Combination of BeautifulSoup, requests, and Trafilatura for content extraction
- **PDF Generation**: ReportLab for creating PDF documents
- **Deployment**: WSGI-compatible with ProxyFix middleware for reverse proxy support

### Frontend Architecture
- **Template Engine**: Jinja2 (Flask's default)
- **CSS Framework**: Bootstrap 5 with dark theme support
- **JavaScript**: Vanilla JavaScript for form validation and UI interactions
- **Icons**: Font Awesome for iconography

### Database Schema
- **ScrapeHistory Model**: Tracks scraping operations with fields for URL, title, scrape date, success status, and error messages

## Key Components

### Core Modules
1. **app.py**: Application factory and configuration
2. **routes.py**: Flask route handlers for web endpoints
3. **web_scraper.py**: Main scraping logic using multiple libraries
4. **link_extractor.py**: Specialized link extraction functionality
5. **pdf_generator.py**: PDF document creation and formatting
6. **models.py**: SQLAlchemy database models

### Web Scraping Pipeline
- URL validation and preprocessing
- Content extraction using Trafilatura for clean text
- Link extraction using BeautifulSoup
- Error handling and retry mechanisms
- User-agent spoofing to avoid blocking

### PDF Generation
- ReportLab-based PDF creation
- Custom styling and formatting
- Support for structured content layout
- Error PDF generation for failed scrapes

## Data Flow

1. **User Input**: URL submission through web form
2. **Validation**: URL format validation and preprocessing
3. **Scraping**: Content and link extraction from target website
4. **Storage**: Scrape history logged to database
5. **Presentation**: Results displayed in web interface
6. **PDF Export**: On-demand PDF generation from scraped data

## External Dependencies

### Python Libraries
- **Flask**: Web framework and routing
- **SQLAlchemy**: Database ORM and migrations
- **BeautifulSoup4**: HTML parsing and navigation
- **Trafilatura**: Clean text extraction from web pages
- **ReportLab**: PDF document generation
- **Requests**: HTTP client for web scraping

### Frontend Dependencies
- **Bootstrap 5**: CSS framework with dark theme
- **Font Awesome**: Icon library
- **Vanilla JavaScript**: Client-side functionality

### Development Dependencies
- **Werkzeug**: WSGI utilities and development server
- **Standard Library**: logging, urllib, datetime modules

## Deployment Strategy

### Configuration
- Environment-based configuration for database URLs and secrets
- Configurable session secrets for production security
- Database connection pooling with health checks

### Production Considerations
- ProxyFix middleware for reverse proxy deployments
- Configurable database backends (SQLite default, PostgreSQL ready)
- Error logging and debugging capabilities
- Session management and security

### Scalability Features
- Database connection pooling
- Request timeout configurations
- Memory-conscious content processing (500KB limit)
- Graceful error handling and recovery

The application is designed to be easily deployable on various platforms with minimal configuration changes, supporting both development and production environments.

## Recent Changes

### August 9, 2025 - Enhanced Comprehensive Scraping Capabilities
- **Increased Runtime Capacity**: Extended comprehensive scraping time limit to 4 minutes (240 seconds) for more thorough scanning
- **Enhanced Scanning Depth**: Restored max pages to 50 and depth to 3 levels for comprehensive website exploration
- **Improved Data Collection**: Increased link collection limit to 10,000 and image collection to 1,000 for extensive content gathering
- **Optimized Performance**: Reduced inter-page delay from 0.1 to 0.05 seconds for faster scanning while maintaining server respect
- **Better Timeout Management**: 30-second buffer before timeout to ensure graceful completion
- **Robust Error Handling**: Specific timeout and connection error handling for individual page requests
- **Session-Based Progress Tracking**: Prevents multiple simultaneous comprehensive scans
- **Worker Timeout Protection**: Enhanced early timeout detection to prevent worker crashes

### August 9, 2025 - Image Scraping, Upload Feature, and LLM-Friendly Display Updates
- **Added Image Scraping**: New feature to extract image URLs, titles/alt text, and display images from websites
- **Image Upload Feature**: New capability to upload multiple images, host them online, and generate PDFs with hosted URLs
- **Enhanced PDF Generation**: PDFs now include actual images (up to 20) with titles and URLs
- **Image Display in Results**: Web interface shows thumbnails of found images with direct URL display
- **CSV Export with Images**: CSV files now include a section for all found images with metadata
- **Comprehensive Image Collection**: During website scanning, images are collected from all visited pages
- **Smart Image Handling**: Automatic image format conversion, resizing, and error handling for broken images
- **LLM-Friendly Display**: All URLs (links and images) now displayed as plain text instead of hyperlinks for better LLM comprehension
- **Direct URL Display**: Image addresses shown in input fields with copy functionality instead of download links
- **Visual Progress Bar**: Added animated progress bar with status updates during PDF generation
- **Interactive Site Preview**: Added modal with iframe to preview websites before PDF generation
- **Image Hosting**: Uploaded images are now hosted on Cloudinary's professional CDN for permanent, reliable external URLs

### July 26, 2025 - Major Feature Additions and Deployment Optimizations
- **Added CSV Export**: Users can now export scraped data as CSV files in addition to PDF
- **Added Comprehensive Website Scraping**: New feature to scrape entire websites by following internal links
- **True Multi-Level Scanning**: Scraper now goes 3 levels deep, following ALL internal links found on each page
- **Deployment Optimizations**: 
  - Balanced scanning: max 30 pages, depth 3, 2-minute timeout
  - Increased link collection limit to 5000 unique links
  - Added runtime monitoring and intelligent link filtering
- **Enhanced UI**: Added dual scraping options (single page vs entire website) with synchronized inputs
- **Complete Link Collection**: Both PDF and CSV exports include ALL links found across all scanned pages