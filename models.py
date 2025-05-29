from app import db
from datetime import datetime

class ScrapeHistory(db.Model):
    """Model to store scraping history for analytics and caching"""
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(2048), nullable=False)
    title = db.Column(db.String(500))
    scrape_date = db.Column(db.DateTime, default=datetime.utcnow)
    success = db.Column(db.Boolean, default=True)
    error_message = db.Column(db.Text)
    
    def __repr__(self):
        return f'<ScrapeHistory {self.url}>'
