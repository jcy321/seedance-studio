# Database Migrations

This directory contains database migration scripts for the Seedance Studio backend.

## Running Migrations

### Method 1: Using Python script (Recommended)

```bash
cd /root/seedance-studio/backend
python -m migrations.run_migration
```

### Method 2: Using SQL directly

```bash
cd /root/seedance-studio/backend
sqlite3 path/to/your/database.db < migrations/001_add_script_and_character_models.sql
```

## Migration History

### 001_add_script_and_character_models.sql
- **Date**: 2026-05-12
- **Description**: Restructure to support multiple scripts per project
- **Changes**:
  - Create `scripts` table
  - Create `characters` table
  - Migrate existing `projects.docx_path` data to `scripts` table
  - Add `script_id` foreign key to `storyboard_segments` table
  - Update existing storyboard segments to link to scripts

## Notes

- The migration preserves existing data by migrating project docx_path to script records
- The `projects.docx_path` column is left in place for backward compatibility but should not be used in new code
- SQLite doesn't support DROP COLUMN, so removing the column would require recreating the table
