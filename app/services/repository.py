"""
Repository/Data Access Layer for database operations
"""
import logging
from typing import Optional, List, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc, asc

from app.models import Page, Post, Comment, SocialMediaUser, PageAnalytics, page_followers, page_employees
from app.schemas import PageCreate, PostCreate, SocialMediaUserCreate
from app.utils.helpers import paginate_query, calculate_engagement_rate

logger = logging.getLogger(__name__)


class PageRepository:
    """Repository for Page operations"""
    
    @staticmethod
    def create_page(db: Session, page: PageCreate) -> Page:
        """Create a new page"""
        db_page = Page(**page.dict())
        db.add(db_page)
        db.commit()
        db.refresh(db_page)
        logger.info(f"Created page: {page.page_id}")
        return db_page
    
    @staticmethod
    def get_page_by_id(db: Session, page_id: str) -> Optional[Page]:
        """Get page by page_id"""
        return db.query(Page).filter(Page.page_id == page_id).first()
    
    @staticmethod
    def get_page_by_url(db: Session, url: str) -> Optional[Page]:
        """Get page by URL"""
        return db.query(Page).filter(Page.url == url).first()
    
    @staticmethod
    def get_all_pages(
        db: Session,
        page: int = 1,
        per_page: int = 20,
        min_followers: Optional[int] = None,
        max_followers: Optional[int] = None,
        industry: Optional[str] = None,
        name: Optional[str] = None
    ) -> Tuple[List[Page], int, int]:
        """
        Get all pages with optional filtering
        
        Returns:
            Tuple of (items, total, pages)
        """
        query = db.query(Page)
        
        # Apply filters
        if min_followers is not None:
            query = query.filter(Page.followers_count >= min_followers)
        
        if max_followers is not None:
            query = query.filter(Page.followers_count <= max_followers)
        
        if industry:
            query = query.filter(Page.industry.ilike(f"%{industry}%"))
        
        if name:
            query = query.filter(Page.name.ilike(f"%{name}%"))
        
        # Order by most recent
        query = query.order_by(desc(Page.created_at))
        
        return paginate_query(query, page, per_page)
    
    @staticmethod
    def update_page(db: Session, page_id: str, **kwargs) -> Optional[Page]:
        """Update page"""
        db_page = PageRepository.get_page_by_id(db, page_id)
        if db_page:
            for key, value in kwargs.items():
                if hasattr(db_page, key):
                    setattr(db_page, key, value)
            db_page.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(db_page)
            logger.info(f"Updated page: {page_id}")
        return db_page
    
    @staticmethod
    def delete_page(db: Session, page_id: str) -> bool:
        """Delete page"""
        db_page = PageRepository.get_page_by_id(db, page_id)
        if db_page:
            db.delete(db_page)
            db.commit()
            logger.info(f"Deleted page: {page_id}")
            return True
        return False
    
    @staticmethod
    def add_follower(db: Session, page_id: str, user_id: int) -> bool:
        """Add follower to page"""
        try:
            db_page = PageRepository.get_page_by_id(db, page_id)
            db_user = SocialMediaUserRepository.get_user_by_id(db, user_id)
            
            if db_page and db_user:
                if db_user not in db_page.followers:
                    db_page.followers.append(db_user)
                    db.commit()
                    logger.info(f"Added follower {user_id} to page {page_id}")
                    return True
        except Exception as e:
            logger.error(f"Error adding follower: {str(e)}")
        
        return False
    
    @staticmethod
    def add_employee(db: Session, page_id: str, user_id: int) -> bool:
        """Add employee to page"""
        try:
            db_page = PageRepository.get_page_by_id(db, page_id)
            db_user = SocialMediaUserRepository.get_user_by_id(db, user_id)
            
            if db_page and db_user:
                if db_user not in db_page.employees:
                    db_page.employees.append(db_user)
                    db.commit()
                    logger.info(f"Added employee {user_id} to page {page_id}")
                    return True
        except Exception as e:
            logger.error(f"Error adding employee: {str(e)}")
        
        return False


class PostRepository:
    """Repository for Post operations"""
    
    @staticmethod
    def create_post(db: Session, post: PostCreate) -> Post:
        """Create a new post"""
        # Calculate engagement rate
        engagement_rate = calculate_engagement_rate(
            post.likes_count,
            post.comments_count,
            post.shares_count,
            post.views_count or 1
        )
        
        post_dict = post.dict()
        post_dict['engagement_rate'] = engagement_rate
        
        db_post = Post(**post_dict)
        db.add(db_post)
        db.commit()
        db.refresh(db_post)
        logger.info(f"Created post: {post.post_id}")
        return db_post
    
    @staticmethod
    def get_post_by_id(db: Session, post_id: int) -> Optional[Post]:
        """Get post by ID"""
        return db.query(Post).filter(Post.id == post_id).first()
    
    @staticmethod
    def get_post_by_post_id(db: Session, post_id: str) -> Optional[Post]:
        """Get post by post_id"""
        return db.query(Post).filter(Post.post_id == post_id).first()
    
    @staticmethod
    def get_page_posts(
        db: Session,
        page_id: str,
        page: int = 1,
        per_page: int = 15
    ) -> Tuple[List[Post], int, int]:
        """Get posts for a page"""
        query = db.query(Post).filter(
            Post.page_id == page_id
        ).order_by(desc(Post.posted_at))
        
        return paginate_query(query, page, per_page)
    
    @staticmethod
    def update_post(db: Session, post_id: str, **kwargs) -> Optional[Post]:
        """Update post metrics"""
        db_post = PostRepository.get_post_by_post_id(db, post_id)
        if db_post:
            for key, value in kwargs.items():
                if hasattr(db_post, key):
                    setattr(db_post, key, value)
            
            # Recalculate engagement rate if metrics changed
            db_post.engagement_rate = calculate_engagement_rate(
                db_post.likes_count,
                db_post.comments_count,
                db_post.shares_count,
                db_post.views_count or 1
            )
            
            db_post.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(db_post)
            logger.info(f"Updated post: {post_id}")
        
        return db_post


class CommentRepository:
    """Repository for Comment operations"""
    
    @staticmethod
    def create_comment(db: Session, post_id: int, content: str, user_id: Optional[int] = None) -> Comment:
        """Create a new comment"""
        comment = Comment(
            comment_id=f"comment_{post_id}_{datetime.utcnow().timestamp()}",
            post_id=post_id,
            user_id=user_id,
            content=content
        )
        db.add(comment)
        db.commit()
        db.refresh(comment)
        logger.info(f"Created comment on post {post_id}")
        return comment
    
    @staticmethod
    def get_post_comments(
        db: Session,
        post_id: int,
        page: int = 1,
        per_page: int = 20
    ) -> Tuple[List[Comment], int, int]:
        """Get comments for a post"""
        query = db.query(Comment).filter(
            Comment.post_id == post_id
        ).order_by(desc(Comment.created_at))
        
        return paginate_query(query, page, per_page)


class SocialMediaUserRepository:
    """Repository for SocialMediaUser operations"""
    
    @staticmethod
    def create_user(db: Session, user: SocialMediaUserCreate) -> SocialMediaUser:
        """Create a new user"""
        db_user = SocialMediaUser(**user.dict())
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        logger.info(f"Created user: {user.username or user.email}")
        return db_user
    
    @staticmethod
    def get_user_by_id(db: Session, user_id: int) -> Optional[SocialMediaUser]:
        """Get user by ID"""
        return db.query(SocialMediaUser).filter(SocialMediaUser.id == user_id).first()
    
    @staticmethod
    def get_user_by_email(db: Session, email: str) -> Optional[SocialMediaUser]:
        """Get user by email"""
        return db.query(SocialMediaUser).filter(SocialMediaUser.email == email).first()
    
    @staticmethod
    def get_user_by_linkedin_id(db: Session, linkedin_id: str) -> Optional[SocialMediaUser]:
        """Get user by LinkedIn ID"""
        return db.query(SocialMediaUser).filter(SocialMediaUser.linkedin_id == linkedin_id).first()
    
    @staticmethod
    def get_or_create_user(db: Session, user_data: dict) -> SocialMediaUser:
        """Get existing user or create new one"""
        # Try to find by linkedin_id
        if user_data.get('linkedin_id'):
            user = SocialMediaUserRepository.get_user_by_linkedin_id(db, user_data['linkedin_id'])
            if user:
                return user
        
        # Try to find by email
        if user_data.get('email'):
            user = SocialMediaUserRepository.get_user_by_email(db, user_data['email'])
            if user:
                return user
        
        # Create new user
        user_schema = SocialMediaUserCreate(**user_data)
        return SocialMediaUserRepository.create_user(db, user_schema)
    
    @staticmethod
    def get_page_followers(
        db: Session,
        page_id: str,
        page: int = 1,
        per_page: int = 20
    ) -> Tuple[List[SocialMediaUser], int, int]:
        """Get followers of a page"""
        query = db.query(SocialMediaUser).join(
            page_followers
        ).filter(
            page_followers.c.page_id == page_id
        )
        
        return paginate_query(query, page, per_page)
    
    @staticmethod
    def get_page_employees(
        db: Session,
        page_id: str,
        page: int = 1,
        per_page: int = 20
    ) -> Tuple[List[SocialMediaUser], int, int]:
        """Get employees of a page"""
        query = db.query(SocialMediaUser).join(
            page_employees
        ).filter(
            page_employees.c.page_id == page_id
        )
        
        return paginate_query(query, page, per_page)


class PageAnalyticsRepository:
    """Repository for PageAnalytics operations"""
    
    @staticmethod
    def create_analytics(db: Session, page_id: str) -> PageAnalytics:
        """Create analytics record for a page"""
        analytics = PageAnalytics(page_id=page_id)
        db.add(analytics)
        db.commit()
        db.refresh(analytics)
        logger.info(f"Created analytics for page: {page_id}")
        return analytics
    
    @staticmethod
    def get_analytics(db: Session, page_id: str) -> Optional[PageAnalytics]:
        """Get analytics for a page"""
        return db.query(PageAnalytics).filter(PageAnalytics.page_id == page_id).first()
    
    @staticmethod
    def update_analytics(
        db: Session,
        page_id: str,
        average_engagement: float = None,
        total_posts: int = None,
        ai_summary: str = None
    ) -> Optional[PageAnalytics]:
        """Update analytics"""
        analytics = PageAnalyticsRepository.get_analytics(db, page_id)
        
        if not analytics:
            analytics = PageAnalyticsRepository.create_analytics(db, page_id)
        
        if average_engagement is not None:
            analytics.average_post_engagement = average_engagement
        
        if total_posts is not None:
            analytics.total_posts_analyzed = total_posts
        
        if ai_summary is not None:
            analytics.ai_summary = ai_summary
            analytics.ai_summary_generated_at = datetime.utcnow()
        
        analytics.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(analytics)
        
        return analytics
