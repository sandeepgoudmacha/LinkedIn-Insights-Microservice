# API Documentation

## Table of Contents
1. [Overview](#overview)
2. [Getting Started](#getting-started)
3. [Authentication](#authentication)
4. [Endpoints](#endpoints)
5. [Request/Response Examples](#requestresponse-examples)
6. [Error Handling](#error-handling)
7. [Best Practices](#best-practices)

## Overview

The LinkedIn Insights Microservice API provides endpoints to:
- Scrape LinkedIn company pages
- Search and filter pages
- Retrieve posts, followers, and employees
- Generate AI-powered insights
- Manage and analyze company data

**Base URL**: `http://localhost:8000/api`

## Getting Started

### 1. Health Check
Verify the API is running:
```bash
curl http://localhost:8000/health
```

### 2. Get All Pages
Retrieve stored pages:
```bash
curl http://localhost:8000/api/pages
```

### 3. Scrape a New Page
```bash
curl -X POST http://localhost:8000/api/pages/scrape \
  -H "Content-Type: application/json" \
  -d '{
    "page_id": "google",
    "depth": 2
  }'
```

## Authentication

Currently, no authentication is required. In production, implement:
- API Key authentication
- JWT tokens
- OAuth2

## Endpoints

### Pages

#### GET /pages
Get all pages with filters and pagination

**Query Parameters**:
| Parameter | Type | Description |
|-----------|------|-------------|
| page | int | Page number (default: 1) |
| per_page | int | Items per page (default: 20, max: 100) |
| min_followers | int | Minimum follower count |
| max_followers | int | Maximum follower count |
| industry | string | Filter by industry |
| name | string | Search by page name |

**Example**:
```bash
GET /pages?page=1&per_page=20&industry=Technology&min_followers=1000
```

#### GET /pages/{page_id}
Get detailed information about a page

**Query Parameters**:
| Parameter | Type | Description |
|-----------|------|-------------|
| include_posts | bool | Include recent posts (default: true) |
| include_followers | bool | Include followers (default: false) |
| include_employees | bool | Include employees (default: false) |

**Example**:
```bash
GET /pages/google?include_posts=true&include_employees=true
```

#### GET /pages/{page_id}/posts
Get posts from a page

**Query Parameters**:
| Parameter | Type | Description |
|-----------|------|-------------|
| page | int | Page number (default: 1) |
| per_page | int | Posts per page (default: 15, max: 50) |
| sort_by | string | Sort by: recent, popular, engagement |

**Example**:
```bash
GET /pages/google/posts?page=1&per_page=15&sort_by=engagement
```

#### GET /pages/{page_id}/followers
Get followers of a page

**Query Parameters**:
| Parameter | Type | Description |
|-----------|------|-------------|
| page | int | Page number (default: 1) |
| per_page | int | Followers per page (default: 20, max: 100) |

#### GET /pages/{page_id}/analytics
Get analytics and AI summary for a page

**Example**:
```bash
GET /pages/google/analytics
```

#### POST /pages/scrape
Scrape and store a new LinkedIn page

**Request Body**:
```json
{
  "page_id": "google",
  "depth": 2
}
```

**Depth Levels**:
- 1: Basic page details only
- 2: Page details + background post scraping
- 3: Full depth including employees and advanced analytics

#### POST /pages/{page_id}/generate-summary
Generate AI summary for a page (async)

**Example**:
```bash
POST /pages/google/generate-summary
```

## Request/Response Examples

### Example 1: Search Pages by Industry

**Request**:
```bash
curl "http://localhost:8000/api/pages?industry=Technology&min_followers=10000&page=1&per_page=10"
```

**Response**:
```json
{
  "total": 45,
  "page": 1,
  "per_page": 10,
  "pages": 5,
  "items": [
    {
      "id": 1,
      "page_id": "google",
      "name": "Google",
      "url": "https://www.linkedin.com/company/google",
      "description": "Google's mission is to organize the world's information...",
      "industry": "Technology",
      "followers_count": 5000000,
      "employees_count": 150000,
      "created_at": "2024-01-15T10:30:00",
      "updated_at": "2024-01-15T10:30:00"
    },
    ...
  ]
}
```

### Example 2: Get Page with Posts

**Request**:
```bash
curl "http://localhost:8000/api/pages/google?include_posts=true"
```

**Response**:
```json
{
  "id": 1,
  "page_id": "google",
  "name": "Google",
  "followers_count": 5000000,
  "employees_count": 150000,
  "posts": [
    {
      "id": 1,
      "post_id": "google_post_1",
      "content": "Excited to announce...",
      "likes_count": 12500,
      "comments_count": 850,
      "shares_count": 420,
      "engagement_rate": 2.77,
      "posted_at": "2024-01-15T09:00:00"
    },
    ...
  ]
}
```

### Example 3: Scrape a New Page

**Request**:
```bash
curl -X POST http://localhost:8000/api/pages/scrape \
  -H "Content-Type: application/json" \
  -d '{
    "page_id": "microsoft",
    "depth": 2
  }'
```

**Response**:
```json
{
  "success": true,
  "message": "Successfully scraped page 'microsoft'",
  "page": {
    "page_id": "microsoft",
    "name": "Microsoft",
    "url": "https://www.linkedin.com/company/microsoft",
    "industry": "Technology",
    "followers_count": 3500000,
    "employees_count": 220000,
    "created_at": "2024-01-15T10:35:00"
  }
}
```

## Error Handling

### Common Error Responses

**404 Not Found**:
```json
{
  "detail": "Page 'nonexistent' not found"
}
```

**422 Validation Error**:
```json
{
  "detail": [
    {
      "loc": ["body", "page_id"],
      "msg": "ensure this value has at least 1 characters",
      "type": "value_error.any_str.min_length"
    }
  ]
}
```

**500 Internal Server Error**:
```json
{
  "detail": "Internal server error"
}
```

## Best Practices

### 1. Pagination
Always use pagination for list endpoints:
```bash
GET /pages?page=1&per_page=20
```

### 2. Filtering
Use filters to reduce data transfer:
```bash
GET /pages?industry=Technology&min_followers=10000
```

### 3. Caching
Responses are cached for 5 minutes. Force refresh by:
- Scraping the page again
- Updating page details
- Waiting for cache expiration

### 4. Rate Limiting
- Not implemented in v1
- Will be added in future versions

### 5. Error Handling
Always check status code:
```python
import requests

response = requests.get('http://localhost:8000/api/pages/google')
if response.status_code == 200:
    data = response.json()
else:
    print(f"Error: {response.status_code}")
    print(response.json())
```

### 6. Async Operations
Some operations run asynchronously:
```bash
# Initiate summary generation
POST /pages/google/generate-summary

# Check results later
GET /pages/google/analytics
```

## Performance Tips

1. **Use specific filters** instead of fetching all pages
2. **Limit results** with per_page parameter
3. **Cache responses** in your application
4. **Use pagination** for large datasets
5. **Include only needed data** with include_* parameters

## Troubleshooting

### Page Not Found
If you get 404 for a page:
1. Verify the page_id is correct
2. Try scraping the page first: `POST /pages/scrape`
3. Check database connection

### Slow Responses
1. Use pagination with smaller per_page values
2. Apply filters to reduce result set
3. Check database indexes
4. Monitor Redis cache status

### Scraping Failures
1. Verify LinkedIn page exists
2. Check network connectivity
3. Review logs for specific errors
4. Try with depth=1 first (basic details only)

## Support

For issues or questions:
1. Check API logs
2. Review this documentation
3. Check Postman collection examples
4. Verify database and Redis connectivity
