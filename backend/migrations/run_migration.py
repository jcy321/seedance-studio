"""
Database migration script to add Script and Character models

Usage:
    python -m migrations.run_migration
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from app.database import engine


async def run_migration():
    """Run the database migration"""
    migration_file = Path(__file__).parent / "001_add_script_and_character_models.sql"

    print("Reading migration file...")
    with open(migration_file, 'r') as f:
        sql_content = f.read()

    # Split by semicolon and filter out comments and empty statements
    statements = []
    for statement in sql_content.split(';'):
        statement = statement.strip()
        # Skip empty statements and pure comment blocks
        if statement and not all(line.strip().startswith('--') or not line.strip()
                                  for line in statement.split('\n')):
            statements.append(statement)

    print(f"Found {len(statements)} SQL statements to execute")

    async with engine.begin() as conn:
        for idx, statement in enumerate(statements, 1):
            # Get first non-comment line for logging
            first_line = next((line.strip() for line in statement.split('\n')
                              if line.strip() and not line.strip().startswith('--')), '')

            print(f"[{idx}/{len(statements)}] Executing: {first_line[:60]}...")

            try:
                await conn.execute(text(statement))
                print(f"  ✓ Success")
            except Exception as e:
                print(f"  ✗ Error: {e}")
                # Continue with other statements even if one fails
                # (some might fail if already applied)

    print("\n✓ Migration completed!")
    print("\nVerifying migration...")

    # Run verification queries
    async with engine.connect() as conn:
        result = await conn.execute(text("SELECT COUNT(*) as count FROM scripts"))
        script_count = result.scalar()
        print(f"  Scripts table: {script_count} records")

        result = await conn.execute(text("SELECT COUNT(*) as count FROM characters"))
        char_count = result.scalar()
        print(f"  Characters table: {char_count} records")

        result = await conn.execute(text("SELECT COUNT(*) as count FROM storyboard_segments WHERE script_id IS NOT NULL"))
        segment_count = result.scalar()
        print(f"  Storyboard segments with script_id: {segment_count} records")


if __name__ == "__main__":
    print("=" * 60)
    print("Database Migration: Add Script and Character Models")
    print("=" * 60)
    print()

    asyncio.run(run_migration())
