# Backend Architecture Refactoring - Summary

## Overview
Successfully restructured the backend to support multiple scripts per project, with proper character management and script-based storyboard organization.

## Changes Completed

### 1. New Database Models

#### Script Model (`app/models/script.py`)
- Represents individual script documents within a project
- Fields:
  - `project_id`: Foreign key to projects
  - `filename`: Original filename
  - `docx_path`: Path to uploaded document
  - `parsing_status`: Enum (PENDING, PARSING, COMPLETED, FAILED)
  - `parsing_progress`, `parsing_total`, `parsing_message`: Progress tracking
  - `parsed_at`: Timestamp when parsing completed
- Relationships:
  - Belongs to Project
  - Has many StoryboardSegments
  - Has many Characters

#### Character Model (`app/models/character.py`)
- Represents characters extracted from scripts
- Fields:
  - `script_id`: Foreign key to scripts
  - `original_name`: Character name from script
  - `alias_name`: Optional alias (e.g., "男角色1")
  - `gender`: Character gender
  - `description`: Character description
  - `has_reference_image`: Boolean flag
  - `reference_image_path`: Path to selected reference image
  - `candidate_images_json`: JSON array of 4 candidate images
  - `user_asset_id`: Optional link to UserAsset
- Relationships:
  - Belongs to Script
  - Optionally links to UserAsset

### 2. Updated Existing Models

#### Project Model (`app/models/project.py`)
- Removed: `docx_path` field (moved to Script model)
- Added: `scripts` relationship (one-to-many)

#### StoryboardSegment Model (`app/models/storyboard.py`)
- Added: `script_id` foreign key
- Added: `script` relationship
- Kept: `project_id` for backward compatibility and quick queries

### 3. New Repositories

#### ScriptRepository (`app/repositories/script_repository.py`)
- `create()`: Create new script record
- `get_by_id()`: Get script by ID
- `get_by_project()`: List all scripts in a project
- `update_parsing_progress()`: Update parsing progress
- `update_status()`: Update parsing status
- `delete()`: Delete script

#### CharacterRepository (`app/repositories/character_repository.py`)
- `create()`: Create new character
- `get_by_id()`: Get character by ID
- `get_by_script()`: List all characters in a script
- `get_characters_with_images()`: Filter characters with reference images
- `get_characters_without_images()`: Filter characters without images
- `update_candidate_images()`: Save 4 candidate images
- `update_reference_image()`: Set selected reference image
- `link_to_asset()`: Link character to UserAsset
- `update()`: Update character details

### 4. New API Endpoints

#### Script Management (`app/api/v1/endpoints/scripts.py`)
- `POST /scripts/projects/{project_id}/upload`: Upload script document
- `GET /scripts/projects/{project_id}/list`: List all scripts in project
- `GET /scripts/{script_id}`: Get script details
- `GET /scripts/{script_id}/parsing-progress`: Get parsing progress
- `DELETE /scripts/{script_id}`: Delete script

#### Character Management (`app/api/v1/endpoints/characters.py`)
- `GET /characters/scripts/{script_id}/list`: List characters (with filter: all/with_image/without_image)
- `GET /characters/{character_id}`: Get character details
- `PUT /characters/{character_id}`: Update character info
- `POST /characters/{character_id}/generate-images`: Generate 4 candidate images
- `POST /characters/{character_id}/select-image`: Select reference image

### 5. Updated API Endpoints

#### Storyboards (`app/api/v1/endpoints/storyboards.py`)
- Added: `GET /scripts/{script_id}/storyboards`: Get storyboards by script
- Kept: `GET /projects/{project_id}/storyboards`: Backward compatibility

### 6. New Schemas

#### ScriptResponse (`app/schemas/script.py`)
- Full script details including parsing status and progress

#### ScriptListItem (`app/schemas/script.py`)
- Lightweight script info for list views

#### CharacterResponse (`app/schemas/character.py`)
- Full character details including images

#### CharacterListItem (`app/schemas/character.py`)
- Lightweight character info for list views

### 7. Database Migration

#### Migration Script (`migrations/001_add_script_and_character_models.sql`)
- Creates `scripts` table
- Creates `characters` table
- Migrates existing `projects.docx_path` to `scripts` table
- Adds `script_id` column to `storyboard_segments`
- Links existing storyboards to migrated scripts
- Creates necessary indexes

#### Migration Runner (`migrations/run_migration.py`)
- Python script to run migration programmatically
- Includes verification queries
- Successfully migrated 3 existing projects and 25 storyboard segments

## Architecture Changes

### Before
```
Project
  ├── docx_path (single document)
  └── StoryboardSegment[]
```

### After
```
Project (folder)
  └── Script[] (multiple documents)
        ├── docx_path
        ├── parsing_status
        ├── StoryboardSegment[]
        └── Character[]
```

## New Workflow

1. **Create Project**: User creates a project (acts as a folder)
2. **Upload Scripts**: User can upload multiple script documents to the project
3. **Parse Scripts**: Each script is parsed independently with real-time progress
4. **Extract Characters**: Characters are automatically extracted during parsing
5. **Manage Characters**: User can view, filter, and generate reference images for characters
6. **View Storyboards**: User clicks on a script to view its storyboards
7. **Generate Videos**: User can select specific storyboards to generate

## Testing Results

✅ Migration ran successfully
✅ Backend server starts without errors
✅ All new models registered correctly
✅ Existing data migrated properly:
  - 3 projects → 3 scripts
  - 25 storyboard segments linked to scripts
  - 0 characters (will be created during new parsing)

## Next Steps (Frontend)

The backend is complete and ready. The frontend needs to be refactored to:

1. **Project Detail Page**: Show list of scripts instead of single upload
2. **Script List View**: Display scripts with parsing status and progress
3. **Script Detail View**: Show storyboards and characters for selected script
4. **Character Management Panel**: Filter and manage character reference images
5. **Selective Generation**: Allow selecting specific storyboards to generate

## API Usage Examples

### Upload a new script
```bash
POST /scripts/projects/1/upload
Content-Type: multipart/form-data
file: script.docx
```

### List scripts in project
```bash
GET /scripts/projects/1/list
Response: [
  {
    "id": 1,
    "filename": "script1.docx",
    "parsing_status": "completed",
    "parsing_progress": 100,
    ...
  }
]
```

### Get storyboards for a script
```bash
GET /scripts/1/storyboards
```

### List characters (filter by image status)
```bash
GET /characters/scripts/1/list?filter=without_image
```

### Generate character images
```bash
POST /characters/1/generate-images
Response: {
  "candidate_images": ["url1", "url2", "url3", "url4"]
}
```

### Select character image
```bash
POST /characters/1/select-image
Body: {"image_index": 2}
```

## Files Created

- `/root/seedance-studio/backend/app/models/script.py`
- `/root/seedance-studio/backend/app/models/character.py`
- `/root/seedance-studio/backend/app/repositories/script_repository.py`
- `/root/seedance-studio/backend/app/repositories/character_repository.py`
- `/root/seedance-studio/backend/app/schemas/script.py`
- `/root/seedance-studio/backend/app/schemas/character.py`
- `/root/seedance-studio/backend/app/api/v1/endpoints/scripts.py`
- `/root/seedance-studio/backend/app/api/v1/endpoints/characters.py`
- `/root/seedance-studio/backend/migrations/001_add_script_and_character_models.sql`
- `/root/seedance-studio/backend/migrations/run_migration.py`
- `/root/seedance-studio/backend/migrations/README.md`

## Files Modified

- `/root/seedance-studio/backend/app/models/project.py`
- `/root/seedance-studio/backend/app/models/storyboard.py`
- `/root/seedance-studio/backend/app/database.py`
- `/root/seedance-studio/backend/app/api/v1/__init__.py`
- `/root/seedance-studio/backend/app/api/v1/endpoints/storyboards.py`
- `/root/seedance-studio/backend/app/repositories/storyboard_repository.py`
