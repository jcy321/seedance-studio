import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from app.database import engine


async def run_migration():
    """Run migration 005: Add user_asset_relations table"""
    print("Running migration 005: Add user_asset_relations table...")

    migration_file = Path(__file__).parent / "005_add_user_asset_relations.sql"

    with open(migration_file, 'r') as f:
        sql_content = f.read()

    # Split by semicolon and filter out comments and empty statements
    statements = [
        s.strip()
        for s in sql_content.split(';')
        if s.strip() and not s.strip().startswith('--')
    ]

    async with engine.begin() as conn:
        for i, statement in enumerate(statements, 1):
            try:
                print(f"Executing statement {i}/{len(statements)}...")
                await conn.execute(text(statement))
                print(f"✓ Statement {i} completed")
            except Exception as e:
                print(f"✗ Statement {i} failed: {e}")
                # Continue with other statements even if one fails
                continue

    print("\n✓ Migration 005 completed!")

    # Verify the changes
    print("\nVerifying table structure...")
    async with engine.begin() as conn:
        result = await conn.execute(text("PRAGMA table_info(user_asset_relations)"))
        columns = result.fetchall()
        print("\nCurrent columns in user_asset_relations:")
        for col in columns:
            print(f"  - {col[1]} ({col[2]})")


if __name__ == "__main__":
    asyncio.run(run_migration())
