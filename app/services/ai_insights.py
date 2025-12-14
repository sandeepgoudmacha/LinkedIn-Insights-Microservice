"""
AI-powered insights and summary service using Google Gemini
"""
import logging
import os
from typing import Optional, Dict, List
import google.generativeai as genai
from datetime import datetime

logger = logging.getLogger(__name__)


class AIInsightService:
    """Service for generating AI-powered insights using Google Gemini"""
    
    def __init__(self):
        self.api_key = os.getenv('GEMINI_API_KEY')
        self.model = os.getenv('GEMINI_MODEL', 'gemini-pro')
        
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.client = genai.GenerativeModel(self.model)
            self.enabled = True
            logger.info(f"AI Insight Service enabled with model: {self.model}")
        else:
            self.enabled = False
            logger.warning("AI Insight Service disabled - no API key provided")
    
    def generate_page_summary(
        self,
        page_name: str,
        description: str,
        industry: str,
        followers_count: int,
        employees_count: int,
        specialties: List[str],
        recent_posts: List[Dict] = None,
        recent_posts_count: int = 0,
        average_engagement: float = 0.0
    ) -> Optional[str]:
        """
        Generate AI summary for a company page
        
        Args:
            page_name: Company name
            description: Company description
            industry: Industry
            followers_count: Number of followers
            employees_count: Number of employees
            specialties: List of specialties
            recent_posts: Recent posts data
            recent_posts_count: Count of recent posts
            average_engagement: Average engagement rate
        
        Returns:
            AI-generated summary or None if failed
        """
        if not self.enabled:
            logger.warning("AI Insight Service is disabled")
            return None
        
        try:
            prompt = self._build_summary_prompt(
                page_name,
                description,
                industry,
                followers_count,
                employees_count,
                specialties,
                recent_posts,
                recent_posts_count,
                average_engagement
            )
            
            system_message = "You are an expert business analyst providing concise, insightful summaries of companies based on their LinkedIn presence. Keep responses to 2-3 paragraphs."
            full_prompt = f"{system_message}\n\n{prompt}"
            
            response = self.client.generate_content(
                full_prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=500,
                    temperature=0.7,
                )
            )
            
            summary = response.text.strip()
            logger.info(f"Generated AI summary for {page_name}")
            return summary
        
        except Exception as e:
            logger.error(f"Gemini API error: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error generating summary: {str(e)}")
            return None
    
    def _build_summary_prompt(
        self,
        page_name: str,
        description: str,
        industry: str,
        followers_count: int,
        employees_count: int,
        specialties: List[str],
        recent_posts: List[Dict] = None,
        recent_posts_count: int = 0,
        average_engagement: float = 0.0
    ) -> str:
        """Build prompt for AI summary generation"""
        
        specialties_str = ", ".join(specialties) if specialties else "Not specified"
        posts_summary = ""
        
        if recent_posts:
            # Summarize recent posts
            post_topics = []
            for post in recent_posts[:3]:  # Top 3 posts
                if post.get('content'):
                    post_topics.append(post['content'][:100])
            posts_summary = f"\n\nRecent post topics:\n" + "\n".join(f"- {topic}" for topic in post_topics)
        
        prompt = f"""
        Analyze and provide insights about this company based on their LinkedIn presence:
        
        Company Name: {page_name}
        Industry: {industry}
        Description: {description[:300] if description else 'Not provided'}
        
        Social Metrics:
        - LinkedIn Followers: {followers_count:,}
        - Employees on LinkedIn: {employees_count:,}
        - Average Post Engagement Rate: {average_engagement:.2f}%
        - Recent Posts Analyzed: {recent_posts_count}
        
        Specialties: {specialties_str}
        {posts_summary}
        
        Please provide:
        1. A brief assessment of the company's industry position and market presence
        2. Analysis of their LinkedIn engagement and audience reach
        3. Insights about their content strategy and company culture (based on posts)
        
        Keep the analysis concise and professional, suitable for business stakeholders.
        """
        
        return prompt.strip()
    
    def analyze_audience_demographics(
        self,
        followers: List[Dict],
        employees: List[Dict]
    ) -> Optional[Dict]:
        """
        Analyze audience demographics and preferences
        
        Args:
            followers: List of follower profiles
            employees: List of employee profiles
        
        Returns:
            Dictionary with demographic insights or None
        """
        if not self.enabled:
            return None
        
        try:
            # Prepare data
            follower_count = len(followers)
            employee_count = len(employees)
            
            # Extract positions/headlines
            follower_positions = [f.get('current_position', 'Unknown') for f in followers if f.get('current_position')]
            employee_headlines = [e.get('headline', 'Unknown') for e in employees if e.get('headline')]
            
            prompt = f"""
            Analyze this company's audience based on their followers and employees:
            
            Total Followers Analyzed: {follower_count}
            Total Employees Analyzed: {employee_count}
            
            Top Follower Positions: {', '.join(set(follower_positions[:10]))}
            
            Employee Headlines: {', '.join(set(employee_headlines[:10]))}
            
            Provide a brief analysis of:
            1. The type of professionals following this company
            2. The expertise and diversity of their team
            3. Potential audience interests based on their follower base
            """
            
            response = self.client.generate_content(
                prompt.strip(),
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=300,
                    temperature=0.6,
                )
            )
            
            analysis = response.text.strip()
            
            return {
                'analysis': analysis,
                'follower_count': follower_count,
                'employee_count': employee_count,
                'generated_at': datetime.utcnow().isoformat()
            }
        
        except Exception as e:
            logger.error(f"Error analyzing audience: {str(e)}")
            return None
    
    def extract_key_insights(
        self,
        engagement_data: Dict,
        growth_data: Dict
    ) -> Optional[List[str]]:
        """
        Extract key business insights from metrics
        
        Args:
            engagement_data: Engagement metrics
            growth_data: Growth/trend data
        
        Returns:
            List of key insights or None
        """
        if not self.enabled:
            return None
        
        try:
            prompt = f"""
            Based on these LinkedIn metrics, provide 3-4 key business insights:
            
            Engagement Metrics:
            - Average Post Engagement: {engagement_data.get('avg_engagement', 0):.2f}%
            - Total Posts: {engagement_data.get('total_posts', 0)}
            - Average Likes: {engagement_data.get('avg_likes', 0)}
            - Average Comments: {engagement_data.get('avg_comments', 0)}
            
            Growth Data:
            - Follower Growth (last 30 days): {growth_data.get('follower_growth', 0)}%
            - Post Frequency: {growth_data.get('post_frequency', 'unknown')}
            
            Provide actionable insights in bullet format (3-4 points max).
            """
            
            response = self.client.generate_content(
                prompt.strip(),
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=250,
                    temperature=0.5,
                )
            )
            
            insights_text = response.text.strip()
            # Split by newlines and bullet points
            insights = [
                line.strip().lstrip('- •*')
                for line in insights_text.split('\n')
                if line.strip()
            ]
            
            return insights
        
        except Exception as e:
            logger.error(f"Error extracting insights: {str(e)}")
            return None
