"""
Page API endpoints
"""
import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import (
    PageResponse,
    PageDetailResponse,
    PageListResponse,
    PostListResponse,
    FollowerListResponse,
    ScrapeRequestSchema,
    ScrapeResponseSchema,
    PageAnalyticsResponse,
    ErrorResponse
)
from app.services import (
    LinkedInScraper,
    PageRepository,
    PostRepository,
    SocialMediaUserRepository,
    PageAnalyticsRepository,
    AIInsightService
)
from app.models import Page, Post
from app.utils import cache_manager, cached

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/pages", tags=["pages"])


# ==================== Page List & Search ====================

@router.get("", response_model=PageListResponse)
async def get_pages(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    min_followers: Optional[int] = Query(None, ge=0, description="Minimum followers"),
    max_followers: Optional[int] = Query(None, ge=0, description="Maximum followers"),
    industry: Optional[str] = Query(None, description="Filter by industry"),
    name: Optional[str] = Query(None, description="Filter by page name"),
    db: Session = Depends(get_db)
):
    """
    Get all pages with filtering and pagination
    
    Query Parameters:
    - page: Page number (default: 1)
    - per_page: Items per page (default: 20, max: 100)
    - min_followers: Minimum follower count
    - max_followers: Maximum follower count
    - industry: Filter by industry (partial match)
    - name: Filter by page name (partial match)
    
    Example: GET /api/pages?page=1&per_page=20&min_followers=1000&industry=Technology
    """
    try:
        items, total, pages = PageRepository.get_all_pages(
            db,
            page=page,
            per_page=per_page,
            min_followers=min_followers,
            max_followers=max_followers,
            industry=industry,
            name=name
        )
        
        return PageListResponse(
            total=total,
            page=page,
            per_page=per_page,
            pages=pages,
            items=[PageResponse.from_orm(item) for item in items]
        )
    
    except Exception as e:
        logger.error(f"Error fetching pages: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


# ==================== Single Page Details ====================

@router.get("/{page_id}", response_model=PageDetailResponse)
async def get_page_detail(
    page_id: str,
    include_posts: bool = Query(True, description="Include posts"),
    include_followers: bool = Query(False, description="Include followers"),
    include_employees: bool = Query(False, description="Include employees"),
    db: Session = Depends(get_db)
):
    """
    Get detailed information about a page
    
    If page not found in database, will attempt to scrape it in real-time.
    
    Query Parameters:
    - include_posts: Include recent posts (default: true)
    - include_followers: Include followers list (default: false)
    - include_employees: Include employees list (default: false)
    """
    try:
        # Try to get from cache first
        cache_key = f"page_detail:{page_id}"
        cached_page = cache_manager.get(cache_key)
        if cached_page:
            logger.debug(f"Cache hit for page {page_id}")
            return cached_page
        
        # Get from database
        db_page = PageRepository.get_page_by_id(db, page_id)
        
        # If not found, try scraping
        if not db_page:
            logger.info(f"Page {page_id} not in DB, attempting to scrape...")
            scraper = LinkedInScraper()
            page_data = await scraper.fetch_page_details(page_id)
            
            if not page_data:
                raise HTTPException(
                    status_code=404,
                    detail=f"Page '{page_id}' not found"
                )
            
            # Store in DB
            from app.schemas import PageCreate
            page_create = PageCreate(**page_data)
            db_page = PageRepository.create_page(db, page_create)
        
        # Build response
        response_data = PageDetailResponse.from_orm(db_page)
        
        # Add posts if requested
        if include_posts:
            posts, _, _ = PostRepository.get_page_posts(db, page_id, page=1, per_page=15)
            response_data.posts = [PostResponse.from_orm(post) for post in posts]
        
        # Add followers if requested
        if include_followers:
            followers, _, _ = SocialMediaUserRepository.get_page_followers(db, page_id)
            response_data.followers = [UserResponse.from_orm(f) for f in followers]
        
        # Add employees if requested
        if include_employees:
            employees, _, _ = SocialMediaUserRepository.get_page_employees(db, page_id)
            response_data.employees = [UserResponse.from_orm(e) for e in employees]
        
        # Cache the result
        cache_manager.set(cache_key, response_data.dict(), ttl=300)
        
        return response_data
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching page {page_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


from app.schemas import SocialMediaUserResponse as UserResponse
from app.schemas import PostResponse


# ==================== Page Posts ====================

@router.get("/{page_id}/posts", response_model=PostListResponse)
async def get_page_posts(
    page_id: str,
    page: int = Query(1, ge=1),
    per_page: int = Query(15, ge=1, le=50),
    sort_by: str = Query("recent", regex="^(recent|popular|engagement)$"),
    db: Session = Depends(get_db)
):
    """
    Get recent posts from a page
    
    Query Parameters:
    - page: Page number (default: 1)
    - per_page: Posts per page (default: 15, max: 50)
    - sort_by: Sort order (recent, popular, engagement)
    """
    try:
        # Verify page exists
        db_page = PageRepository.get_page_by_id(db, page_id)
        if not db_page:
            raise HTTPException(status_code=404, detail="Page not found")
        
        items, total, pages = PostRepository.get_page_posts(db, page_id, page, per_page)
        
        # Sort by preference
        if sort_by == "popular":
            items = sorted(items, key=lambda x: x.likes_count, reverse=True)
        elif sort_by == "engagement":
            items = sorted(items, key=lambda x: x.engagement_rate, reverse=True)
        
        return PostListResponse(
            total=total,
            page=page,
            per_page=per_page,
            pages=pages,
            items=[PostResponse.from_orm(item) for item in items]
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching posts for page {page_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


# ==================== Page Followers ====================

@router.get("/{page_id}/followers", response_model=FollowerListResponse)
async def get_page_followers(
    page_id: str,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Get followers/audience of a page
    
    Query Parameters:
    - page: Page number (default: 1)
    - per_page: Followers per page (default: 20, max: 100)
    """
    try:
        # Verify page exists
        db_page = PageRepository.get_page_by_id(db, page_id)
        if not db_page:
            raise HTTPException(status_code=404, detail="Page not found")
        
        items, total, pages = SocialMediaUserRepository.get_page_followers(db, page_id, page, per_page)
        
        return FollowerListResponse(
            total=total,
            page=page,
            per_page=per_page,
            pages=pages,
            items=[UserResponse.from_orm(item) for item in items]
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching followers for page {page_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


# ==================== Page Employees ====================

@router.get("/{page_id}/employees", response_model=FollowerListResponse)
async def get_page_employees(
    page_id: str,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Get employees list for a page
    
    Query Parameters:
    - page: Page number (default: 1)
    - per_page: Employees per page (default: 20, max: 100)
    """
    try:
        # Verify page exists
        db_page = PageRepository.get_page_by_id(db, page_id)
        if not db_page:
            raise HTTPException(status_code=404, detail="Page not found")
        
        items, total, pages = SocialMediaUserRepository.get_page_employees(db, page_id, page, per_page)
        
        return FollowerListResponse(
            total=total,
            page=page,
            per_page=per_page,
            pages=pages,
            items=[UserResponse.from_orm(item) for item in items]
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching employees for page {page_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


# ==================== Page Analytics & Summary ====================

@router.get("/{page_id}/analytics", response_model=PageAnalyticsResponse)
async def get_page_analytics(
    page_id: str,
    db: Session = Depends(get_db)
):
    """
    Get analytics and AI summary for a page
    
    Returns engagement metrics and AI-generated insights if available.
    """
    try:
        # Verify page exists
        db_page = PageRepository.get_page_by_id(db, page_id)
        if not db_page:
            raise HTTPException(status_code=404, detail="Page not found")
        
        # Get or create analytics
        analytics = PageAnalyticsRepository.get_analytics(db, page_id)
        if not analytics:
            analytics = PageAnalyticsRepository.create_analytics(db, page_id)
        
        return PageAnalyticsResponse.from_orm(analytics)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching analytics for page {page_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


# ==================== Scraping ====================

@router.post("/scrape", response_model=ScrapeResponseSchema)
async def scrape_page(
    request: ScrapeRequestSchema,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Scrape and store a LinkedIn page with REAL data
    
    Uses ScraperAPI (recommended) or Selenium Browser for actual LinkedIn data
    
    Priority:
    1. ScraperAPI (most reliable, handles anti-scraping)
    2. Selenium Browser (JS rendering)
    3. Direct HTTP (might work)
    
    Returns REAL data or error - never returns fake/demo data
    """
    try:
        # Check if already exists
        existing = PageRepository.get_page_by_id(db, request.page_id)
        if existing:
            return ScrapeResponseSchema(
                success=True,
                message="Page already exists in database",
                page=PageResponse.from_orm(existing)
            )
        
        # Scrape with REAL methods only
        logger.info(f"\n{'='*70}")
        logger.info(f"🔴 REQUEST: Scraping REAL LinkedIn data for: {request.page_id}")
        logger.info(f"{'='*70}")
        
        scraper = LinkedInScraper(use_browser=True)  # Use browser as fallback
        page_data = await scraper.fetch_page_details(request.page_id)
        
        if not page_data:
            logger.error(f"❌ FAILED: Could not scrape REAL data for '{request.page_id}'")
            return ScrapeResponseSchema(
                success=False,
                message=f"Failed to scrape REAL data for '{request.page_id}'",
                error="Could not fetch actual LinkedIn data. Solution: 1) Make sure Chrome/Chromium is installed, 2) Check internet connection, 3) Try again (LinkedIn may be rate limiting)"
            )
        
        # Validate we got real data (not demo with fake numbers)
        if page_data.get('followers_count', 0) <= 100:
            logger.warning(f"⚠️  Suspicious: Got only {page_data.get('followers_count')} followers - might be demo data")
        
        # Store in database
        from app.schemas import PageCreate
        page_create = PageCreate(**page_data)
        db_page = PageRepository.create_page(db, page_create)
        
        logger.info(f"✅ SUCCESS: Stored REAL LinkedIn data for {request.page_id}")
        logger.info(f"   Followers: {page_data.get('followers_count', 0)}")
        logger.info(f"   Employees: {page_data.get('employees_count', 0)}")
        logger.info(f"{'='*70}\n")
        
        # Scrape posts in background
        if request.depth >= 2:
            background_tasks.add_task(
                _scrape_posts_background,
                request.page_id,
                db
            )
        
        return ScrapeResponseSchema(
            success=True,
            message=f"✅ Successfully scraped REAL LinkedIn data for '{request.page_id}'",
            page=PageResponse.from_orm(db_page)
        )
    
    except Exception as e:
        logger.error(f"Error scraping page {request.page_id}: {str(e)}")
        return ScrapeResponseSchema(
            success=False,
            message="Error during scraping",
            error=str(e)
        )


async def _scrape_posts_background(page_id: str, db: Session):
    """Background task to scrape posts"""
    try:
        scraper = LinkedInScraper()
        posts_data = await scraper.fetch_posts(page_id, limit=20)
        
        for post_data in posts_data:
            # Check if post already exists
            if not PostRepository.get_post_by_post_id(db, post_data['post_id']):
                from app.schemas import PostCreate
                post_create = PostCreate(**post_data)
                
                # Upload image if exists
                
                PostRepository.create_post(db, post_create)
        
        logger.info(f"Scraped {len(posts_data)} posts for page {page_id}")
    
    except Exception as e:
        logger.error(f"Error scraping posts for {page_id}: {str(e)}")


# ==================== AI Insights ====================

@router.post("/{page_id}/generate-summary")
async def generate_page_summary(
    page_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Generate AI summary for a page
    
    Uses Google Gemini to generate insights about the company.
    Runs asynchronously in the background.
    """
    db_page = PageRepository.get_page_by_id(db, page_id)
    if not db_page:
        raise HTTPException(status_code=404, detail="Page not found")
    
    # Extract data before passing to background task
    page_data = {
        'page_id': page_id,
        'name': db_page.name,
        'description': db_page.description,
        'industry': db_page.industry,
        'followers_count': db_page.followers_count,
        'employees_count': db_page.employees_count,
        'specialties': db_page.specialties or []
    }
    
    # Add background task with page data, not the session
    background_tasks.add_task(
        _generate_summary_background,
        page_data
    )
    
    return {
        "success": True,
        "message": "Summary generation started. Check analytics endpoint for results."
    }


def _generate_summary_background(page_data: dict):
    """Background task to generate AI summary"""
    try:
        from app.database import SessionLocal
        
        # Create a new session for the background task
        db = SessionLocal()
        
        try:
            ai_service = AIInsightService()
            page_id = page_data['page_id']
            
            # If AI is disabled, just skip
            if not ai_service.enabled:
                logger.warning(f"AI service disabled for {page_id}")
                return
            
            # Get recent posts for context
            try:
                posts, _, _ = PostRepository.get_page_posts(db, page_id, page=1, per_page=5)
            except:
                posts = []
            
            # Generate summary
            summary = ai_service.generate_page_summary(
                page_name=page_data['name'],
                description=page_data['description'],
                industry=page_data['industry'],
                followers_count=page_data['followers_count'],
                employees_count=page_data['employees_count'],
                specialties=page_data['specialties'],
                recent_posts=[{'content': p.content, 'engagement_rate': p.engagement_rate} for p in posts],
                recent_posts_count=len(posts),
                average_engagement=sum(p.engagement_rate for p in posts) / len(posts) if posts else 0
            )
            
            if summary:
                PageAnalyticsRepository.update_analytics(
                    db,
                    page_id,
                    ai_summary=summary
                )
                logger.info(f"Generated AI summary for page {page_id}")
            else:
                logger.info(f"No AI summary generated for {page_id} (AI service disabled or returned None)")
        
        except Exception as e:
            logger.error(f"Error in background summary task: {str(e)}", exc_info=True)
        
        finally:
            try:
                db.close()
            except:
                pass
    
    except Exception as e:
        logger.error(f"Error in background task setup: {str(e)}", exc_info=True)
