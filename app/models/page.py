"""
Database models for LinkedIn Insights Microservice
"""
from datetime import datetime
from typing import Optional, List
from sqlalchemy import (
    Column, String, Integer, Float, Text, DateTime, 
    ForeignKey, Table, Boolean, JSON, Index, UniqueConstraint
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, Mapped, mapped_column
from enum import Enum

Base = declarative_base()


# Association tables for many-to-many relationships
page_followers = Table(
    'page_followers',
    Base.metadata,
    Column('page_id', String(50), ForeignKey('pages.page_id'), primary_key=True),
    Column('user_id', Integer, ForeignKey('social_media_users.id'), primary_key=True)
)

page_employees = Table(
    'page_employees',
    Base.metadata,
    Column('page_id', String(50), ForeignKey('pages.page_id'), primary_key=True),
    Column('user_id', Integer, ForeignKey('social_media_users.id'), primary_key=True)
)


class Page(Base):
    """LinkedIn Company Page Model"""
    __tablename__ = "pages"
    
    id = Column(Integer, primary_key=True, index=True)
    page_id = Column(String(100), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False, index=True)
    url = Column(String(500), unique=True, nullable=False)
    linkedin_id = Column(String(100), unique=True, nullable=True)
    description = Column(Text, nullable=True)
    profile_picture_url = Column(String(500), nullable=True)
    profile_picture_s3_url = Column(String(500), nullable=True)  # S3 stored image
    website = Column(String(500), nullable=True)
    industry = Column(String(100), nullable=True, index=True)
    company_size = Column(String(50), nullable=True)
    headquarters = Column(String(255), nullable=True)
    founded_year = Column(Integer, nullable=True)
    specialties = Column(JSON, nullable=True)  # Store as JSON array
    
    # Metrics
    followers_count = Column(Integer, default=0, index=True)
    employees_count = Column(Integer, default=0)
    
    # Relationships
    posts: Mapped[List["Post"]] = relationship("Post", back_populates="page", cascade="all, delete-orphan")
    followers: Mapped[List["SocialMediaUser"]] = relationship(
        "SocialMediaUser",
        secondary=page_followers,
        backref="following_pages"
    )
    employees: Mapped[List["SocialMediaUser"]] = relationship(
        "SocialMediaUser",
        secondary=page_employees,
        backref="employer_pages"
    )
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_scraped_at = Column(DateTime, nullable=True)
    
    __table_args__ = (
        Index('idx_page_id_name', 'page_id', 'name'),
        Index('idx_followers_industry', 'followers_count', 'industry'),
    )
    
    def __repr__(self):
        return f"<Page(page_id={self.page_id}, name={self.name}, followers={self.followers_count})>"


class Post(Base):
    """LinkedIn Post Model"""
    __tablename__ = "posts"
    
    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(String(100), unique=True, nullable=False, index=True)
    page_id = Column(String(100), ForeignKey('pages.page_id'), nullable=False, index=True)
    
    content = Column(Text, nullable=False)
    image_url = Column(String(500), nullable=True)
    image_s3_url = Column(String(500), nullable=True)  # S3 stored image
    
    # Metrics
    likes_count = Column(Integer, default=0)
    comments_count = Column(Integer, default=0)
    shares_count = Column(Integer, default=0)
    views_count = Column(Integer, default=0, nullable=True)
    
    # Engagement
    engagement_rate = Column(Float, default=0.0)
    
    # Relationships
    page: Mapped["Page"] = relationship("Page", back_populates="posts")
    comments: Mapped[List["Comment"]] = relationship("Comment", back_populates="post", cascade="all, delete-orphan")
    
    # Metadata
    posted_at = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_post_page_date', 'page_id', 'posted_at'),
    )
    
    def __repr__(self):
        return f"<Post(post_id={self.post_id}, page_id={self.page_id}, likes={self.likes_count})>"


class Comment(Base):
    """Post Comment Model"""
    __tablename__ = "comments"
    
    id = Column(Integer, primary_key=True, index=True)
    comment_id = Column(String(100), unique=True, nullable=False)
    post_id = Column(Integer, ForeignKey('posts.id'), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey('social_media_users.id'), nullable=True)
    
    content = Column(Text, nullable=False)
    
    # Metrics
    likes_count = Column(Integer, default=0)
    
    # Relationships
    post: Mapped["Post"] = relationship("Post", back_populates="comments")
    user: Mapped[Optional["SocialMediaUser"]] = relationship("SocialMediaUser", back_populates="comments")
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<Comment(comment_id={self.comment_id}, post_id={self.post_id})>"


class SocialMediaUser(Base):
    """LinkedIn User/Employee Model"""
    __tablename__ = "social_media_users"
    
    id = Column(Integer, primary_key=True, index=True)
    linkedin_id = Column(String(100), unique=True, nullable=True, index=True)
    username = Column(String(255), nullable=True)
    email = Column(String(255), unique=True, nullable=True, index=True)
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    headline = Column(String(255), nullable=True)
    profile_picture_url = Column(String(500), nullable=True)
    profile_picture_s3_url = Column(String(500), nullable=True)
    
    # Professional info
    current_position = Column(String(255), nullable=True)
    current_company = Column(String(255), nullable=True)
    location = Column(String(255), nullable=True)
    summary = Column(Text, nullable=True)
    
    # Metrics
    followers_count = Column(Integer, default=0)
    connections_count = Column(Integer, default=0)
    
    # Relationships
    comments: Mapped[List["Comment"]] = relationship("Comment", back_populates="user")
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_user_linkedin_email', 'linkedin_id', 'email'),
    )
    
    def __repr__(self):
        return f"<SocialMediaUser(username={self.username}, email={self.email})>"


class PageAnalytics(Base):
    """Store analytics and summaries for pages"""
    __tablename__ = "page_analytics"
    
    id = Column(Integer, primary_key=True, index=True)
    page_id = Column(String(100), ForeignKey('pages.page_id'), unique=True, nullable=False, index=True)
    
    # Engagement metrics
    average_post_engagement = Column(Float, default=0.0)
    total_posts_analyzed = Column(Integer, default=0)
    most_engaged_post_id = Column(String(100), nullable=True)
    
    # Follower demographics
    follower_count_trend = Column(JSON, nullable=True)  # Historical data
    top_follower_industries = Column(JSON, nullable=True)
    
    # AI Summary
    ai_summary = Column(Text, nullable=True)
    ai_summary_generated_at = Column(DateTime, nullable=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<PageAnalytics(page_id={self.page_id})>"
