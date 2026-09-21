#!/usr/bin/env python3
"""
Migration 006: Add candidate_images_json to scenes and items
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from app.core.config import settings

def run_migration():
    # Convert async URL to sync URL for migration
    db_url = settings.database_url.replace('sqlite+aiosqlite:', 'sqlite:')
    engine = create_engine(db_url)

    with engine.connect() as conn:
        print("Running migration 006...")

        # Read SQL file
        sql_file = os.path.join(os.path.dirname(__file__), "006_add_candidate_images_to_assets.sql")
        with open(sql_file, 'r') as f:
            sql_content = f.read()

        # Split by semicolon and execute each statement
        statements = [s.strip() for s in sql_content.split(';') if s.strip() and not s.strip().startswith('--')]

        for statement in statements:
            if statement:
                print(f"Executing: {statement[:100]}...")
                conn.execute(text(statement))

        conn.commit()
        print("Migration 006 completed successfully!")

if __name__ == "__main__":
    run_migration()
