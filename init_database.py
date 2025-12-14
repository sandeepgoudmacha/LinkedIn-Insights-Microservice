#!/usr/bin/env python
"""
Force database table initialization
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

print("\n" + "="*70)
print("DATABASE INITIALIZATION")
print("="*70)

try:
    print("\n1. Loading database configuration...")
    from app.database import init_db
    print("   OK - Database module loaded")
    
    print("\n2. Creating database tables...")
    init_db()
    print("   OK - Tables created successfully")
    
    print("\n3. Verifying tables...")
    from app.database import engine
    from sqlalchemy import inspect, text
    
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    
    print(f"   Found {len(tables)} tables:")
    for table in tables:
        print(f"     - {table}")
    
    print("\n" + "="*70)
    print("SUCCESS: Database initialized!")
    print("="*70)
    print("\nNext: Restart the server and try scraping")
    print("  uvicorn app.main:app --reload")
    print("\n")
    
except Exception as e:
    print(f"\nERROR: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
