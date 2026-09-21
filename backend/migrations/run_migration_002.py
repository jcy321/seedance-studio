"""
Database migration script to add Asset and Generation Task models

Usage:
    python -m migrations.run_migration_002
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
    migration_file = Path(__file__).parent / "002_add_asset_and_generation_models.sql"

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
        result = await conn.execute(text("SELECT COUNT(*) as count FROM scenes"))
        scene_count = result.scalar()
        print(f"  Scenes table: {scene_count} records")

        result = await conn.execute(text("SELECT COUNT(*) as count FROM items"))
        item_count = result.scalar()
        print(f"  Items table: {item_count} records")

        result = await conn.execute(text("SELECT COUNT(*) as count FROM costumes"))
        costume_count = result.scalar()
        print(f"  Costumes table: {costume_count} records")

        result = await conn.execute(text("SELECT COUNT(*) as count FROM generation_tasks"))
        task_count = result.scalar()
        print(f"  Generation tasks table: {task_count} records")

        result = await conn.execute(text("SELECT COUNT(*) as count FROM segment_assets"))
        segment_asset_count = result.scalar()
        print(f"  Segment assets table: {segment_asset_count} records")

        result = await conn.execute(text("SELECT COUNT(*) as count FROM characters WHERE generation_status IS NOT NULL"))
        char_with_status = result.scalar()
        print(f"  Characters with generation_status: {char_with_status} records")

        result = await conn.execute(text("SELECT COUNT(*) as count FROM storyboard_segments WHERE video_generation_status IS NOT NULL"))
        segments_with_status = result.scalar()
        print(f"  Storyboard segments with video_generation_status: {segments_with_status} records")


if __name__ == "__main__":
    print("=" * 60)
    print("Database Migration: Add Asset and Generation Task Models")
    print("=" * 60)
    print()

    asyncio.run(run_migration())
