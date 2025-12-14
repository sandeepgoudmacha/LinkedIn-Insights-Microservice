#!/usr/bin/env python
"""
Add Google to the database with realistic LinkedIn metrics
"""
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.models import Page
from app.database import SessionLocal

def add_google():
    """Add Google company page to database"""
    session = SessionLocal()
    
    try:
        # Check if Google already exists
        existing = session.query(Page).filter_by(page_id='google').first()
        
        if existing:
            print("✓ Google already in database")
            return
        
        # Create Google page with realistic metrics
        google = Page(
            page_id='google',
            name='Google',
            url='https://www.linkedin.com/company/google',
            description='Google is an American multinational technology company that specializes in Internet-related services and products. 10M+ employees across the globe.',
            profile_picture_url='https://media.licdn.com/dms/image/v2/C4D0BAQHsAVZ2v0-fpA/company-logo_200_200/company-logo_200_200/0/1677616397000/google_logo?e=2147483647&v=beta&t=',
            website='google.com',
            industry='Software Development',
            company_size='10,001+ employees',
            headquarters='Mountain View, California',
            founded_year=1998,
            followers_count=19200000,  # Realistic Google followers count
            employees_count=190234,    # Realistic Google employees
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        session.add(google)
        session.commit()
        print("✅ Google added to database")
        print(f"   - Followers: 19,200,000")
        print(f"   - Employees: 190,234")
        print(f"   - ID: {google.id}")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        session.rollback()
        raise
    finally:
        session.close()

if __name__ == "__main__":
    add_google()
