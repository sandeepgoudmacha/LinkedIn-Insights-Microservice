#!/bin/bash

# Clear old demo/fake data from database before testing real scraping

echo "=========================================="
echo "🗑️  Clearing old demo data..."
echo "=========================================="

# Remove the database file
if [ -f linkedin_insights.db ]; then
    rm linkedin_insights.db
    echo "✅ Deleted linkedin_insights.db"
else
    echo "⚠️  Database file not found (already clean)"
fi

echo ""
echo "=========================================="
echo "✅ Database cleared!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Restart server: uvicorn app.main:app --reload"
echo "2. Database will be recreated automatically"
echo "3. Scrape fresh: curl -X POST http://localhost:8000/api/pages/scrape -H 'Content-Type: application/json' -d '{\"page_id\": \"eightfoldai\"}'"
echo ""
