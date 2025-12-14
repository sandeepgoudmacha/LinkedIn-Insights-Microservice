"""
Utility tests
"""
import pytest
from app.utils.helpers import (
    calculate_engagement_rate,
    format_large_number,
    truncate_text,
    parse_follower_range,
    SearchHelper
)


class TestEngagementRate:
    """Test engagement rate calculation"""
    
    def test_engagement_rate_basic(self):
        """Test basic engagement rate calculation"""
        rate = calculate_engagement_rate(
            likes=100,
            comments=50,
            shares=20,
            views=1000
        )
        assert rate == 17.0  # (100 + 50 + 20) / 1000 * 100
    
    def test_engagement_rate_zero_views(self):
        """Test with zero views"""
        rate = calculate_engagement_rate(
            likes=100,
            comments=50,
            shares=20,
            views=0
        )
        assert rate == 0.0


class TestFormatNumber:
    """Test number formatting"""
    
    def test_format_thousands(self):
        """Test formatting thousands"""
        assert format_large_number(1500) == "1.5K"
        assert format_large_number(999) == "999"
    
    def test_format_millions(self):
        """Test formatting millions"""
        assert format_large_number(1_500_000) == "1.5M"
    
    def test_format_billions(self):
        """Test formatting billions"""
        assert format_large_number(1_500_000_000) == "1.5B"


class TestTruncateText:
    """Test text truncation"""
    
    def test_truncate_long_text(self):
        """Test truncating long text"""
        text = "a" * 200
        result = truncate_text(text, 100)
        assert len(result) <= 100
        assert result.endswith("...")
    
    def test_no_truncate_short_text(self):
        """Test short text not truncated"""
        text = "short text"
        result = truncate_text(text, 100)
        assert result == text


class TestParseFollowerRange:
    """Test follower range parsing"""
    
    def test_parse_k_range(self):
        """Test parsing K range"""
        result = parse_follower_range("1k-10k")
        assert result == (1000, 10000)
    
    def test_parse_m_range(self):
        """Test parsing M range"""
        result = parse_follower_range("1m-5m")
        assert result == (1_000_000, 5_000_000)
    
    def test_invalid_range(self):
        """Test invalid range"""
        result = parse_follower_range("invalid")
        assert result is None


class TestSearchHelper:
    """Test search and similarity"""
    
    def test_exact_match(self):
        """Test exact match similarity"""
        score = SearchHelper.similarity_score("hello", "hello")
        assert score == 1.0
    
    def test_partial_match(self):
        """Test partial match"""
        score = SearchHelper.similarity_score("hello", "helloworld")
        assert score == 0.9
    
    def test_no_match(self):
        """Test no match"""
        score = SearchHelper.similarity_score("abc", "xyz")
        assert 0 <= score <= 1
    
    def test_similar_search(self):
        """Test similar search"""
        items = ["google", "facebook", "microsoft", "apple"]
        results = SearchHelper.similar_search("goo", items, threshold=0.5)
        assert "google" in results or len(results) > 0
