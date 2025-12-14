"""
API endpoint tests
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import get_db
from app.models import Base
from app.schemas import PageCreate, PostCreate


# Use in-memory SQLite for testing
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


class TestHealth:
    """Health check tests"""
    
    def test_health_check(self):
        """Test health endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
    
    def test_api_version(self):
        """Test version endpoint"""
        response = client.get("/api/version")
        assert response.status_code == 200
        data = response.json()
        assert "version" in data
        assert "app" in data


class TestPages:
    """Page endpoint tests"""
    
    def test_get_pages_empty(self):
        """Test getting pages when empty"""
        response = client.get("/api/pages")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["items"] == []
    
    def test_pagination(self):
        """Test pagination parameters"""
        response = client.get("/api/pages?page=1&per_page=10")
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 1
        assert data["per_page"] == 10
    
    def test_invalid_page(self):
        """Test invalid page number"""
        response = client.get("/api/pages?page=0")
        # Should be adjusted to 1 internally
        assert response.status_code == 200
    
    def test_get_nonexistent_page(self):
        """Test getting nonexistent page"""
        response = client.get("/api/pages/nonexistent")
        assert response.status_code == 404


class TestScraping:
    """Scraping endpoint tests"""
    
    def test_scrape_request_invalid(self):
        """Test scrape with invalid page_id"""
        response = client.post(
            "/api/pages/scrape",
            json={"page_id": ""}
        )
        assert response.status_code == 422  # Validation error
    
    def test_scrape_request_valid_format(self):
        """Test scrape request format"""
        response = client.post(
            "/api/pages/scrape",
            json={
                "page_id": "google",
                "depth": 2
            }
        )
        # May fail due to network, but shouldn't be a validation error
        assert response.status_code in [200, 400, 404]


class TestFiltering:
    """Filtering tests"""
    
    def test_filter_by_industry(self):
        """Test filtering by industry"""
        response = client.get("/api/pages?industry=technology")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data["items"], list)
    
    def test_filter_by_name(self):
        """Test filtering by name"""
        response = client.get("/api/pages?name=google")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data["items"], list)
    
    def test_filter_by_followers(self):
        """Test filtering by follower count"""
        response = client.get("/api/pages?min_followers=1000&max_followers=100000")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data["items"], list)


@pytest.fixture(autouse=True)
def cleanup():
    """Cleanup after each test"""
    yield
    # Clear all tables
    for table in reversed(Base.metadata.sorted_tables):
        engine.execute(table.delete())
