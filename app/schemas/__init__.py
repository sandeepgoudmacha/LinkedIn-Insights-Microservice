"""
Pydantic schemas for request/response validation
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, HttpUrl, field_validator


class SocialMediaUserBase(BaseModel):
    """Base user schema"""
    linkedin_id: Optional[str] = None
    username: Optional[str] = None
    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    headline: Optional[str] = None
    profile_picture_url: Optional[str] = None
    current_position: Optional[str] = None
    current_company: Optional[str] = None
    location: Optional[str] = None


class SocialMediaUserCreate(SocialMediaUserBase):
    """Schema for creating a user"""
    pass


class SocialMediaUserResponse(SocialMediaUserBase):
    """Schema for user response"""
    id: int
    followers_count: int = 0
    connections_count: int = 0
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class CommentBase(BaseModel):
    """Base comment schema"""
    content: str = Field(..., min_length=1, max_length=5000)
    likes_count: int = Field(default=0, ge=0)


class CommentCreate(CommentBase):
    """Schema for creating a comment"""
    pass


class CommentResponse(CommentBase):
    """Schema for comment response"""
    id: int
    comment_id: str
    post_id: int
    user_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    user: Optional[SocialMediaUserResponse] = None
    
    class Config:
        from_attributes = True


class PostBase(BaseModel):
    """Base post schema"""
    content: str = Field(..., min_length=1, max_length=10000)
    image_url: Optional[str] = None
    image_s3_url: Optional[str] = None
    likes_count: int = Field(default=0, ge=0)
    comments_count: int = Field(default=0, ge=0)
    shares_count: int = Field(default=0, ge=0)
    views_count: Optional[int] = Field(default=None, ge=0)


class PostCreate(PostBase):
    """Schema for creating a post"""
    page_id: str
    posted_at: datetime


class PostUpdate(BaseModel):
    """Schema for updating post metrics"""
    likes_count: Optional[int] = None
    comments_count: Optional[int] = None
    shares_count: Optional[int] = None
    views_count: Optional[int] = None


class PostResponse(PostBase):
    """Schema for post response"""
    id: int
    post_id: str
    page_id: str
    engagement_rate: float
    posted_at: datetime
    created_at: datetime
    updated_at: datetime
    comments: List[CommentResponse] = []
    
    class Config:
        from_attributes = True


class PageBase(BaseModel):
    """Base page schema"""
    page_id: str = Field(..., min_length=1, max_length=100)
    name: str = Field(..., min_length=1, max_length=255)
    url: str = Field(..., min_length=1, max_length=500)
    linkedin_id: Optional[str] = None
    description: Optional[str] = None
    profile_picture_url: Optional[str] = None
    website: Optional[str] = None
    industry: Optional[str] = None
    company_size: Optional[str] = None
    headquarters: Optional[str] = None
    founded_year: Optional[int] = None
    specialties: Optional[List[str]] = None
    followers_count: int = Field(default=0, ge=0)
    employees_count: int = Field(default=0, ge=0)


class PageCreate(PageBase):
    """Schema for creating a page"""
    pass


class PageUpdate(BaseModel):
    """Schema for updating a page"""
    followers_count: Optional[int] = None
    employees_count: Optional[int] = None
    description: Optional[str] = None
    specialties: Optional[List[str]] = None


class PageResponse(PageBase):
    """Schema for page response"""
    id: int
    followers_count: int
    employees_count: int
    profile_picture_s3_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    last_scraped_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class PageDetailResponse(PageResponse):
    """Detailed page response with related data"""
    posts: List[PostResponse] = []
    followers: List[SocialMediaUserResponse] = []
    employees: List[SocialMediaUserResponse] = []
    
    class Config:
        from_attributes = True


class PageListResponse(BaseModel):
    """Paginated list response"""
    total: int
    page: int
    per_page: int
    pages: int
    items: List[PageResponse]


class PostListResponse(BaseModel):
    """Paginated posts list response"""
    total: int
    page: int
    per_page: int
    pages: int
    items: List[PostResponse]


class FollowerListResponse(BaseModel):
    """Paginated followers list response"""
    total: int
    page: int
    per_page: int
    pages: int
    items: List[SocialMediaUserResponse]


class PageAnalyticsResponse(BaseModel):
    """Page analytics response"""
    page_id: str
    average_post_engagement: float
    total_posts_analyzed: int
    most_engaged_post_id: Optional[str] = None
    ai_summary: Optional[str] = None
    ai_summary_generated_at: Optional[datetime] = None
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ScrapeRequestSchema(BaseModel):
    """Schema for scrape request"""
    page_id: str = Field(..., min_length=1, max_length=100)
    depth: int = Field(default=2, ge=1, le=5)  # How deep to scrape (posts to fetch, etc.)


class ScrapeResponseSchema(BaseModel):
    """Schema for scrape response"""
    success: bool
    message: str
    page: Optional[PageResponse] = None
    error: Optional[str] = None


class FilterSchema(BaseModel):
    """Schema for filtering pages"""
    min_followers: Optional[int] = Field(None, ge=0)
    max_followers: Optional[int] = Field(None, ge=0)
    industry: Optional[str] = None
    name: Optional[str] = None  # Similar search
    company_size: Optional[str] = None


class ErrorResponse(BaseModel):
    """Standard error response"""
    success: bool = False
    error: str
    details: Optional[dict] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
