"""
Generate sample posts, followers, and employees for existing pages
This adds realistic demo data to the database for API testing
"""
import os
import sys
from datetime import datetime, timedelta
from random import randint, choice, random
from sqlalchemy.orm import sessionmaker

# Fix encoding for Windows console
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Add app to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.models import (
    Page, Post, SocialMediaUser, PageAnalytics
)
from app.database import engine, SessionLocal

# Sample data templates
POST_TEMPLATES = [
    "Excited to announce our latest innovation in {industry}! With AI and cloud technology, we're transforming how businesses operate. Read more: {link}",
    "Thank you to our amazing team for their dedication and hard work! 👏 Together we're building the future of {industry}.",
    "Strategic partnership announcement: {company1} and {company2} are joining forces to deliver enterprise solutions at scale. #innovation",
    "New whitepaper: Top 5 trends shaping {industry} in 2025. Download insights on AI, automation, and digital transformation: {link}",
    "Milestone moment: {milestone}. We're grateful for our {followers}+ community of innovators, leaders, and changemakers.",
    "Introducing {feature} - designed to help enterprises scale faster. Early customers seeing 40% efficiency gains. Learn more: {link}",
    "We're hiring across {location} and beyond! Join our team to shape the future of {industry}. Apply now: {link}",
    "Proud to support {initiative}. Our commitment to responsible AI and ethical innovation is core to everything we do.",
    "Breaking: New investment in {region} to accelerate cloud and AI infrastructure. {amount} committed over {timeframe} years.",
    "Real-time intelligence: How leading companies use {technology} to serve millions. Great case study from {partner}. {link}",
]

FOLLOWER_NAMES = [
    "John Smith", "Sarah Johnson", "Mike Chen", "Emma Wilson",
    "Alex Kumar", "Lisa Anderson", "James Brown", "Rachel Lee",
    "David Martinez", "Sophie Taylor", "Robert Wilson", "Maria Garcia",
    "Christopher Lee", "Jennifer Davis", "Daniel Rodriguez", "Amanda Jones",
    "Matthew Miller", "Nicole Anderson", "Andrew Thompson", "Katherine White"
]

EMPLOYEE_NAMES = [
    "Alice Johnson", "Bob Smith", "Carol White", "David Brown",
    "Emma Wilson", "Frank Miller", "Grace Lee", "Henry Davis",
    "Ivy Martinez", "Jack Taylor", "Karen Anderson", "Leo Garcia",
    "Megan Johnson", "Nathan Williams", "Olivia Thomas", "Paul Jackson",
    "Quinn Roberts", "Rachel Edwards", "Samuel Collins", "Tina Stewart"
]

POSITIONS = [
    "Software Engineer", "Product Manager", "Data Scientist",
    "UX/UI Designer", "Sales Manager", "Marketing Manager",
    "DevOps Engineer", "Business Analyst", "QA Engineer",
    "Team Lead", "VP Engineering", "Chief Product Officer"
]

LOCATIONS = [
    "San Francisco, CA",
    "New York, NY",
    "Seattle, WA",
    "Austin, TX",
    "Boston, MA",
    "Los Angeles, CA",
    "Chicago, IL"
]

INDUSTRIES = [
    "Technology",
    "Software Development",
    "Artificial Intelligence",
    "Cloud Computing",
    "Data Analytics"
]

def generate_posts(page, num_posts=15):
    """Generate sample posts for a page with REALISTIC engagement"""
    posts = []
    now = datetime.utcnow()
    
    # More realistic engagement ratios based on actual LinkedIn data
    # Large companies (10M+ followers): 0.05-0.5% engagement
    # Medium companies (100K-1M followers): 0.5-2% engagement
    # Small companies (10K followers): 2-5% engagement
    
    follower_millions = page.followers_count / 1_000_000
    
    if follower_millions > 10:
        # Large companies like Microsoft, Google, Amazon
        likes_range = (150, 5000)
        comments_range = (10, 200)
        shares_range = (5, 150)
        views_multiplier = (5, 15)  # views = likes * multiplier
    elif follower_millions > 1:
        # Medium companies
        likes_range = (100, 2000)
        comments_range = (5, 100)
        shares_range = (2, 80)
        views_multiplier = (3, 10)
    else:
        # Smaller companies
        likes_range = (50, 1000)
        comments_range = (3, 50)
        shares_range = (1, 40)
        views_multiplier = (2, 8)
    
    for i in range(num_posts):
        days_ago = randint(1, 30)  # More recent posts
        post_date = now - timedelta(days=days_ago)
        
        template = choice(POST_TEMPLATES)
        try:
            content = template.format(
                industry=page.industry or "technology",
                company1=choice(["Microsoft", "Google", "AWS", "Azure"]),
                company2=choice(["Infosys", "Cognizant", "TCS", "Wipro"]),
                link="msft.it/6042tcWNm",
                milestone=f"${randint(5, 20)}B investment announcement",
                followers=f"{page.followers_count/1_000_000:.1f}M",
                feature=choice(["Copilot", "Azure AI", "Fabric", "365 AI"]),
                location=page.headquarters or "multiple locations",
                initiative="responsible AI",
                region=choice(["India", "Southeast Asia", "Europe", "Americas"]),
                amount=f"${randint(5, 20)}B",
                timeframe=randint(2, 5),
                partner=choice(["Swiggy", "Cognizant", "Infosys"]),
                technology=choice(["Microsoft Fabric", "Azure OpenAI", "Copilot", "365"])
            )
        except KeyError:
            # Fallback if template doesn't have all placeholders
            content = f"Important update from {page.name}: advancing technology and innovation in {page.industry or 'technology'}"
        
        likes = randint(*likes_range)
        comments = randint(*comments_range)
        shares = randint(*shares_range)
        views = likes * randint(*views_multiplier)
        
        post = Post(
            post_id=f"post_{page.page_id}_{i}",
            page_id=page.page_id,
            content=content[:500],
            likes_count=likes,
            comments_count=comments,
            shares_count=shares,
            views_count=views,
            posted_at=post_date
        )
        
        # Calculate engagement rate (typical LinkedIn: 0.1-2%)
        total_interactions = likes + comments + shares
        engagement_percent = (total_interactions / max(page.followers_count, 1)) * 100
        post.engagement_rate = round(engagement_percent, 2)
        
        posts.append(post)
    
    return posts


def generate_followers(page, num_followers=25):
    """Generate sample followers for a page"""
    followers = []
    
    for i in range(num_followers):
        username = f"{choice(FOLLOWER_NAMES).lower().replace(' ', '_')}_{i}"
        name = choice(FOLLOWER_NAMES)
        
        follower = SocialMediaUser(
            username=username,
            first_name=name.split()[0],
            last_name=name.split()[1] if len(name.split()) > 1 else "",
            headline=f"{choice(POSITIONS)} at {choice(['TechCorp', 'DataSystems', 'CloudInnovate', 'AILabs'])}",
            location=choice(LOCATIONS),
            connections_count=randint(100, 2000),
            followers_count=randint(0, 5000)
        )
        
        followers.append(follower)
    
    return followers


def generate_employees(page, num_employees=None):
    """Generate sample employees for a page"""
    if num_employees is None:
        # Generate based on company size
        if page.employees_count:
            num_employees = min(max(page.employees_count // 100, 5), 20)  # Sample of actual size
        else:
            num_employees = 15
    
    employees = []
    
    for i in range(num_employees):
        username = f"{choice(EMPLOYEE_NAMES).lower().replace(' ', '_')}_{i}"
        name = choice(EMPLOYEE_NAMES)
        
        employee = SocialMediaUser(
            username=username,
            first_name=name.split()[0],
            last_name=name.split()[1] if len(name.split()) > 1 else "",
            headline=choice(POSITIONS),
            current_position=choice(POSITIONS),
            current_company=page.name,
            location=page.headquarters or choice(LOCATIONS),
            connections_count=randint(200, 1000),
            followers_count=randint(10, 1000)
        )
        
        employees.append(employee)
    
    return employees


def generate_analytics(page, session):
    """Generate or update analytics for a page"""
    # Get posts to calculate metrics
    posts = session.query(Post).filter_by(page_id=page.page_id).all()
    
    if not posts:
        average_engagement = 0
        most_engaged_post = None
    else:
        engagement_rates = [p.engagement_rate or 0 for p in posts]
        average_engagement = round(sum(engagement_rates) / len(engagement_rates), 2)
        most_engaged_post = max(posts, key=lambda p: p.engagement_rate or 0).post_id
    
    analytics = PageAnalytics(
        page_id=page.page_id,
        total_posts_analyzed=len(posts),
        average_post_engagement=average_engagement,
        most_engaged_post_id=most_engaged_post,
        follower_count_trend=[
            {
                "date": (datetime.utcnow() - timedelta(days=90)).strftime("%Y-%m-%d"),
                "followers": max(0, page.followers_count - randint(5000, 20000))
            },
            {
                "date": (datetime.utcnow() - timedelta(days=60)).strftime("%Y-%m-%d"),
                "followers": max(0, page.followers_count - randint(2000, 10000))
            },
            {
                "date": (datetime.utcnow() - timedelta(days=30)).strftime("%Y-%m-%d"),
                "followers": max(0, page.followers_count - randint(500, 5000))
            },
            {
                "date": datetime.utcnow().strftime("%Y-%m-%d"),
                "followers": page.followers_count
            }
        ],
        top_follower_industries=[
            page.industry or "Technology",
            "Information Technology",
            "Human Resources"
        ]
    )
    
    return analytics


def main():
    """Main function to generate sample data"""
    Session = SessionLocal
    session = Session()
    
    try:
        print("=" * 70)
        print("🔵 GENERATING SAMPLE DATA FOR API ENDPOINTS")
        print("=" * 70)
        
        # Get all existing pages
        pages = session.query(Page).all()
        
        if not pages:
            print("❌ No pages found in database!")
            print("   First, scrape some pages using: POST /api/pages/scrape")
            return
        
        for page in pages:
            print(f"\n📝 Generating data for: {page.name} ({page.page_id})")
            
            # Check if data already exists
            existing_posts = session.query(Post).filter_by(page_id=page.page_id).count()
            
            if existing_posts > 0:
                print(f"   ✓ Data already exists - Skipping")
                continue
            
            # Generate posts
            print(f"   • Generating 15 sample posts...")
            posts = generate_posts(page, num_posts=15)
            session.add_all(posts)
            
            # Generate followers
            print(f"   • Generating 25 sample followers...")
            followers = generate_followers(page, num_followers=25)
            session.add_all(followers)
            page.followers.extend(followers)
            
            # Generate employees
            print(f"   • Generating 20 sample employees...")
            employees = generate_employees(page, num_employees=20)
            session.add_all(employees)
            page.employees.extend(employees)
            
            # Generate analytics
            print(f"   • Generating analytics...")
            session.flush()  # Make posts available for analytics calculation
            
            # Check if analytics already exists
            existing_analytics = session.query(PageAnalytics).filter_by(page_id=page.page_id).first()
            if not existing_analytics:
                analytics = generate_analytics(page, session)
                session.add(analytics)
            else:
                print(f"     Analytics already exists - Skipping")
            
            # Commit this page's data
            session.commit()
            
            print(f"   ✅ Successfully generated data for {page.name}")
            print(f"      - Posts: 15")
            print(f"      - Followers: 25")
            print(f"      - Employees: 20")
            print(f"      - Analytics: Generated")
        
        print("\n" + "=" * 70)
        print("✅ SAMPLE DATA GENERATION COMPLETE!")
        print("=" * 70)
        print("\n🚀 Now your endpoints will return data:")
        print("   GET  /api/pages/{page_id}/posts")
        print("   GET  /api/pages/{page_id}/followers")
        print("   GET  /api/pages/{page_id}/employees")
        print("   GET  /api/pages/{page_id}/analytics")
        print("\n📊 Try these commands:")
        print("   curl http://localhost:8000/api/pages/eightfoldai/posts")
        print("   curl http://localhost:8000/api/pages/eightfoldai/followers")
        print("   curl http://localhost:8000/api/pages/eightfoldai/employees")
        print("   curl http://localhost:8000/api/pages/eightfoldai/analytics")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        session.rollback()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    main()
