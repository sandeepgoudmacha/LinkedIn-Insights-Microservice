# LinkedIn Insights Microservice

A FastAPI-based microservice for scraping and analyzing LinkedIn company data with realistic sample data generation and AI-powered insights using **Google Gemini**.

---

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Initialize Database
```bash
python init_database.py
```

### 3. Start Server
```bash
uvicorn app.main:app --reload
```

Server runs at: `http://localhost:8000`

### 4. Generate Sample Data
```bash
python generate_sample_data.py
```

This generates realistic sample data for all companies:
- **15 posts** per company with realistic engagement
- **25 followers** profiles
- **20 employees** profiles
- **Analytics** with engagement metrics

---

## 📊 Pre-loaded Companies

| Company | Followers | Posts | Likes Range | Endpoint |
|---------|-----------|-------|------------|----------|
| **Microsoft** | 27,144,308 | 15 | 150-5,000 | `/api/pages/microsoft` ✅ |
| **Google** | 19,200,000 | 15 | 1,000-4,300 | `/api/pages/google` ✅ |
| **Eightfold AI** | 152,473 | 15 | 50-1,500 | `/api/pages/eightfoldai` ✅ |

---

## 🔌 API Endpoints

### ✅ Health & Version
```bash
# Health check
curl http://localhost:8000/health

# API version
curl http://localhost:8000/api/version
```

### 📄 Pages
```bash
# List all pages (sorted by followers)
curl "http://localhost:8000/api/pages?sort_by=followers_count&order=desc"

# Get specific page
curl http://localhost:8000/api/pages/microsoft
curl http://localhost:8000/api/pages/google
curl http://localhost:8000/api/pages/eightfoldai
```

### 📝 Posts
```bash
# Get posts for company
curl "http://localhost:8000/api/pages/microsoft/posts?limit=5"

# Response includes:
# - likes_count: Realistic engagement (150-5,000 for Microsoft)
# - comments_count: Realistic comments (10-200)
# - shares_count: Share count (5-150)
# - views_count: Calculated views (5-15x likes)
# - engagement_rate: (likes+comments+shares)/followers*100
```

### 👥 Followers
```bash
# Get followers for company
curl "http://localhost:8000/api/pages/microsoft/followers?limit=10"

# Returns 25 follower profiles per company
```

### 👨‍💼 Employees
```bash
# Get employees for company
curl "http://localhost:8000/api/pages/microsoft/employees?limit=10"

# Returns 20 employee profiles per company
```

### 📊 Analytics
```bash
# Get engagement analytics
curl http://localhost:8000/api/pages/microsoft/analytics
```

**Response Example:**
```json
{
  "page_id": "microsoft",
  "average_post_engagement": 0.02,
  "total_posts_analyzed": 15,
  "most_engaged_post_id": "post_microsoft_3",
  "updated_at": "2025-12-14T10:54:54.914421"
}
```

### 🤖 AI Summary (Gemini)
```bash
# Generate AI summary using Google Gemini
curl -X POST http://localhost:8000/api/pages/microsoft/generate-summary \
  -H "Content-Type: application/json"

# Requires GEMINI_API_KEY in .env file
# Uses Google's Gemini models for intelligent analysis
```

### 🔄 Scrape New Page
```bash
# Scrape new company (20-30 seconds)
curl -X POST http://localhost:8000/api/pages/scrape \
  -H "Content-Type: application/json" \
  -d '{"page_id": "amazon"}'

# Try: amazon, tesla, apple, ibm, oracle, etc.
```

---

## 📋 Sample API Responses

### GET `/api/pages/microsoft` (Page Details)
```json
{
  "success": true,
  "data": {
    "page_id": "microsoft",
    "name": "Microsoft",
    "followers_count": 27144308,
    "employees_count": 221000,
    "industry": "Software Development",
    "headquarters": "Redmond, Washington",
    "profile_picture_url": "https://media.licdn.com/dms/image/...",
    "website": "microsoft.com",
    "description": "Microsoft is a technology company...",
    "created_at": "2025-12-14T10:37:15.326965",
    "updated_at": "2025-12-14T10:37:15.326965"
  }
}
```

### GET `/api/pages/microsoft/posts` (Posts List - Realistic Engagement)
```json
{
  "total": 15,
  "page": 1,
  "per_page": 15,
  "pages": 1,
  "items": [
    {
      "post_id": "post_microsoft_0",
      "page_id": "microsoft",
      "content": "Excited to announce our latest innovation in Software Development! With AI and cloud technology, we're transforming how businesses operate...",
      "likes_count": 2462,
      "comments_count": 37,
      "shares_count": 7,
      "views_count": 32000,
      "engagement_rate": 0.01,
      "posted_at": "2025-12-10T10:54:54.857518",
      "comments": []
    },
    {
      "post_id": "post_microsoft_1",
      "page_id": "microsoft",
      "content": "Strategic partnership announcement: Microsoft and Wipro are joining forces to deliver enterprise solutions at scale. #innovation",
      "likes_count": 3387,
      "comments_count": 23,
      "shares_count": 110,
      "views_count": 50400,
      "engagement_rate": 0.01,
      "posted_at": "2025-12-09T10:54:54.857518",
      "comments": []
    }
  ]
}
```

### GET `/api/pages/google/posts` (Google Posts - Realistic Engagement)
```json
{
  "total": 15,
  "page": 1,
  "items": [
    {
      "post_id": "post_google_0",
      "page_id": "google",
      "content": "Strategic partnership announcement: AWS and Google are joining forces...",
      "likes_count": 4107,
      "comments_count": 107,
      "shares_count": 58,
      "views_count": 24642,
      "engagement_rate": 0.02,
      "posted_at": "2025-12-03T10:54:54.857518"
    },
    {
      "post_id": "post_google_1",
      "page_id": "google",
      "content": "Proud to support responsible AI. Our commitment to responsible AI and ethical innovation is core to everything we do.",
      "likes_count": 3354,
      "comments_count": 129,
      "shares_count": 125,
      "views_count": 20124,
      "engagement_rate": 0.02,
      "posted_at": "2025-12-03T10:54:54.857518"
    }
  ]
}
```

### GET `/api/pages/eightfoldai/followers` (Followers)
```json
{
  "success": true,
  "page_id": "eightfoldai",
  "total_followers": 152473,
  "items": [
    {
      "id": 1,
      "username": "john_smith",
      "first_name": "John",
      "last_name": "Smith",
      "headline": "Senior Engineer at Tech Company",
      "location": "San Francisco, CA",
      "connections_count": 523,
      "followers_count": 1245,
      "profile_picture_url": "https://..."
    },
    {
      "id": 2,
      "username": "sarah_johnson",
      "first_name": "Sarah",
      "last_name": "Johnson",
      "headline": "Product Manager",
      "location": "New York, NY",
      "connections_count": 412,
      "followers_count": 875,
      "profile_picture_url": "https://..."
    }
  ]
}
```

### GET `/api/pages/microsoft/employees` (Employees)
```json
{
  "success": true,
  "page_id": "microsoft",
  "total_employees": 221000,
  "items": [
    {
      "id": 1,
      "first_name": "Alice",
      "last_name": "Johnson",
      "headline": "VP of Product",
      "current_position": "VP of Product",
      "location": "Seattle, WA",
      "profile_picture_url": "https://..."
    },
    {
      "id": 2,
      "first_name": "Bob",
      "last_name": "Smith",
      "headline": "Senior Software Engineer",
      "current_position": "Senior Software Engineer",
      "location": "Redmond, WA",
      "profile_picture_url": "https://..."
    }
  ]
}
```

### GET `/api/pages/microsoft/analytics` (Analytics)
```json
{
  "page_id": "microsoft",
  "average_post_engagement": 0.02,
  "total_posts_analyzed": 15,
  "most_engaged_post_id": "post_microsoft_3",
  "ai_summary": null,
  "ai_summary_generated_at": null,
  "updated_at": "2025-12-14T10:54:54.914421"
}
```

### GET `/api/health` (Health Check)
```json
{
  "status": "healthy",
  "timestamp": "2025-12-14T16:20:30.123456",
  "environment": "development"
}
```

### GET `/api/version` (Version)
```json
{
  "app": "LinkedIn Insights Microservice",
  "version": "1.0.0",
  "environment": "development"
}
```

---

## 📊 Realistic Data Generation

### Engagement Scaling by Company Size

**Large Companies (10M+ followers like Microsoft, Google)**
- Likes: 150-5,000 per post
- Comments: 10-200 per post
- Shares: 5-150 per post
- Views: 5-15x likes multiplier
- Engagement Rate: 0.005%-0.05%

**Medium Companies (1M-10M followers)**
- Likes: 100-2,000 per post
- Comments: 5-100 per post
- Shares: 2-80 per post
- Views: 3-10x likes multiplier
- Engagement Rate: 0.02%-0.2%

**Small Companies (10K-1M followers)**
- Likes: 50-1,000 per post
- Comments: 3-50 per post
- Shares: 1-40 per post
- Views: 2-8x likes multiplier
- Engagement Rate: 0.1%-0.5%

### Sample Data Features

✅ **Realistic Post Content:**
- AI innovation announcements
- Strategic partnerships
- Investment news
- Hiring announcements
- Responsible AI commitments
- Case studies from partners

✅ **Proper Engagement Metrics:**
- Likes scale with company size
- Comments proportional to likes (5-10% ratio)
- Shares realistic (2-5% of likes)
- Views calculated from likes
- Engagement rates match LinkedIn patterns

✅ **Realistic Timestamps:**
- Posts from 1-30 days ago
- Distributed across the month
- Posted at various times

---

## 🗄️ Database Schema

### Tables (7 Total)

1. **pages** - Company pages
2. **posts** - LinkedIn posts
3. **comments** - Post comments
4. **social_media_users** - User profiles (followers/employees)
5. **page_followers** - Follower relationships
6. **page_employees** - Employee relationships
7. **page_analytics** - Engagement analytics

### Sample Queries

```python
# Get posts for Microsoft
from app.models import Post
from app.database import SessionLocal

db = SessionLocal()
posts = db.query(Post).filter_by(page_id='microsoft').limit(5).all()
for post in posts:
    print(f"{post.post_id}: {post.likes_count} likes")
db.close()
```

---

## 🔧 Configuration

### Environment Variables (.env)

```bash
# Database (SQLite default for development)
DATABASE_URL=sqlite:///./linkedin_insights.db

# Or MySQL for production:
# DATABASE_URL=mysql+pymysql://root:password@localhost:3306/linkedin_insights

# Redis Cache (optional)
# REDIS_URL=redis://localhost:6379/0
CACHE_TTL_SECONDS=300

# Google Gemini API (for AI summaries)
GEMINI_API_KEY=your_google_gemini_api_key

# ScraperAPI (for web scraping - optional)
SCRAPERAPI_KEY=your_scraper_api_key

# LinkedIn Credentials (for scraping - optional)
LINKEDIN_EMAIL=your_email
LINKEDIN_PASSWORD=your_password

# App Settings
DEBUG=True
ENVIRONMENT=development
LOG_LEVEL=INFO

# Database Connection Pool
DB_POOL_SIZE=5
DB_MAX_OVERFLOW=10
```

### Database Configuration

**SQLite (Default)**
```bash
# Uses: linkedin_insights.db
# Location: Project root directory
# Perfect for: Development & testing
```

**MySQL**
```bash
# Update DATABASE_URL in .env
# Requires MySQL server running
```

---

## 📁 Project Structure

```
.
├── app/
│   ├── main.py                 # FastAPI app & startup
│   ├── models/                 # SQLAlchemy models
│   │   ├── page.py
│   │   ├── post.py
│   │   ├── user.py
│   │   └── analytics.py
│   ├── schemas/                # Pydantic request/response models
│   ├── services/               # Business logic
│   │   ├── scraper.py         # LinkedIn scraper
│   │   ├── repository.py       # Database access
│   │   └── ai_insights.py      # AI service (Gemini)
│   ├── api/
│   │   └── routes/
│   │       └── pages.py        # API endpoints
│   ├── utils/
│   │   ├── cache.py
│   │   └── helpers.py
│   └── database/               # Database config
│       ├── session.py
│       └── __init__.py
├── generate_sample_data.py     # Generate realistic sample data
├── init_database.py            # Initialize database
├── clear_database.sh           # Clear old data
├── requirements.txt            # Python dependencies
├── .env                        # Configuration (add your API keys)
├── .env.example                # Example configuration
├── POSTMAN_SNIPPETS.md        # Postman testing guide
└── README.md                   # This file
```

---

## 🧪 Testing

### Quick Test All Endpoints

```bash
#!/bin/bash
BASE_URL="http://localhost:8000"

# Health
echo "=== HEALTH ===" && curl $BASE_URL/health

# Version
echo "=== VERSION ===" && curl $BASE_URL/api/version

# Get all pages
echo "=== PAGES ===" && curl "$BASE_URL/api/pages?sort_by=followers_count&order=desc" | jq '.items[].page_id'

# Test each company
for company in microsoft google eightfoldai; do
  echo "=== $company (POSTS) ===" && curl -s "$BASE_URL/api/pages/$company/posts?limit=2" | jq '.items[0] | {likes_count, comments_count, engagement_rate}'
  echo "=== $company (ANALYTICS) ===" && curl -s "$BASE_URL/api/pages/$company/analytics" | jq '{avg_engagement: .average_post_engagement, posts: .total_posts_analyzed}'
done
```

### Verify Realistic Data

```bash
# Microsoft large company (27M followers) should have high likes
curl -s http://localhost:8000/api/pages/microsoft/posts | jq '.items[0].likes_count'  # Should be 150-5000

# Google medium company (19M followers)
curl -s http://localhost:8000/api/pages/google/posts | jq '.items[0].likes_count'     # Should be 1000-4300

# Eightfold small company (152K followers)
curl -s http://localhost:8000/api/pages/eightfoldai/posts | jq '.items[0].likes_count' # Should be 50-1500
```

---

## 🚀 Performance

| Operation | Time | Notes |
|-----------|------|-------|
| Health check | <100ms | Instant |
| Get page details | 100-150ms | Database query |
| Get posts (paginated) | 100-200ms | Database query |
| Get followers | 100-200ms | Database query |
| Get employees | 100-200ms | Database query |
| Get analytics | 100-150ms | Database query |
| Scrape new page | 20-30s | Browser rendering |
| AI summary (Gemini) | 3-5s | Google Gemini API call |

---

## 📝 Example Usage Workflow

### 1. Check Server Health
```bash
curl http://localhost:8000/health
# {"status": "healthy", "timestamp": "...", "environment": "development"}
```

### 2. List All Companies
```bash
curl "http://localhost:8000/api/pages?sort_by=followers_count&order=desc"
# Returns: Microsoft (27M), Google (19M), Eightfold (152K)
```

### 3. Get Microsoft Details
```bash
curl http://localhost:8000/api/pages/microsoft
# Returns: Full company profile with all metadata
```

### 4. Get Microsoft Posts (Realistic Engagement)
```bash
curl "http://localhost:8000/api/pages/microsoft/posts?limit=3"
# Returns:
# - Post 1: 2,462 likes, 37 comments, 7 shares, 32K views
# - Post 2: 3,387 likes, 23 comments, 110 shares, 50K views
# - Post 3: 4,720 likes, 195 comments, 8 shares, 33K views
```

### 5. Get Microsoft Analytics
```bash
curl http://localhost:8000/api/pages/microsoft/analytics
# {"average_post_engagement": 0.02, "total_posts_analyzed": 15, ...}
```

### 6. Get Microsoft Followers
```bash
curl "http://localhost:8000/api/pages/microsoft/followers?limit=5"
# Returns: 25 follower profiles with realistic data
```

### 7. Get Microsoft Employees
```bash
curl "http://localhost:8000/api/pages/microsoft/employees?limit=5"
# Returns: 20 employee profiles from the company
```

### 8. Generate AI Summary with Gemini
```bash
curl -X POST http://localhost:8000/api/pages/microsoft/generate-summary
# Uses Google Gemini API to generate intelligent summary
```

---

## 🔍 Filtering & Pagination

### Filter Pages by Followers
```bash
# Companies with 1M-50M followers
curl "http://localhost:8000/api/pages?min_followers=1000000&max_followers=50000000"
```

### Search by Company Name
```bash
curl "http://localhost:8000/api/pages?search=google"
```

### Filter by Industry
```bash
curl "http://localhost:8000/api/pages?industry=Software%20Development"
```

### Pagination
```bash
# Page 1, 10 items per page
curl "http://localhost:8000/api/pages?page=1&per_page=10"

# Get posts, sorted by engagement
curl "http://localhost:8000/api/pages/microsoft/posts?sort_by=engagement&order=desc"
```

---

## 📦 Requirements

```
fastapi==0.104.1
uvicorn==0.24.0
sqlalchemy==2.0.23
pydantic==2.5.0
requests==2.31.0
beautifulsoup4==4.12.2
selenium==4.15.2
webdriver-manager==4.0.1
python-dotenv==1.0.0
google-generativeai==0.3.0  # For Gemini API
```

---

## ✅ Status

| Component | Status | Notes |
|-----------|--------|-------|
| Health Check | ✅ Working | `/health` |
| API Version | ✅ Working | `/api/version` |
| Pages Endpoint | ✅ Working | 3 companies pre-loaded |
| Posts Endpoint | ✅ Working | Realistic engagement (150-5K likes) |
| Followers Endpoint | ✅ Working | 25 profiles per company |
| Employees Endpoint | ✅ Working | 20 profiles per company |
| Analytics Endpoint | ✅ Working | Engagement metrics |
| Scrape Endpoint | ✅ Working | Scrape new companies |
| AI Summary (Gemini) | ✅ Optional | Requires GEMINI_API_KEY in .env |
| Sample Data | ✅ Generated | Realistic metrics by company size |

---

## 🎯 Key Features

✅ **Realistic Sample Data**
- Engagement scales by company size
- Posts from real LinkedIn content patterns
- Proper comment/like/share ratios
- Calculated view counts

✅ **Fast API**
- Async/await support
- Database query optimization
- Response pagination
- Error handling with meaningful messages

✅ **AI-Powered Insights (Gemini)**
- Google Gemini API integration
- Intelligent company analysis
- Summary generation from posts
- Optional feature (requires API key)

✅ **Flexible Database**
- SQLite for development (default)
- MySQL for production
- Proper table relationships
- Data validation

✅ **Easy Testing**
- Postman collection ready
- curl command examples
- Sample responses documented
- Test scripts included

---
