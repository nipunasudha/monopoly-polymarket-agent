"""
Migration runner for database migrations.
"""
import importlib
import inspect
from pathlib import Path
from typing import List, Dict, Any
from agents.connectors.database import Database
import logging

logger = logging.getLogger(__name__)


class MigrationRecord:
    """Tracks which migrations have been run."""
    
    __tablename__ = "migrations"
    
    def __init__(self, name: str, applied_at: str):
        self.name = name
        self.applied_at = applied_at


def get_migration_files() -> List[Path]:
    """Get all migration files in order."""
    migrations_dir = Path(__file__).parent
    migration_files = sorted(migrations_dir.glob("*.py"))
    # Exclude __init__.py and runner.py
    return [f for f in migration_files if f.name not in ["__init__.py", "runner.py"]]


def get_applied_migrations(db: Database) -> List[str]:
    """Get list of applied migration names from database."""
    try:
        from sqlalchemy import text
        with db.get_session() as session:
            # Try to query migrations table
            result = session.execute(text("SELECT name FROM migrations ORDER BY name"))
            return [row[0] for row in result]
    except Exception:
        # Table doesn't exist or query failed, return empty list
        return []


def create_migrations_table(db: Database):
    """Create migrations tracking table if it doesn't exist."""
    try:
        from sqlalchemy import text
        with db.get_session() as session:
            session.execute(text("""
                CREATE TABLE IF NOT EXISTS migrations (
                    name TEXT PRIMARY KEY,
                    applied_at TEXT NOT NULL
                )
            """))
            session.commit()
    except Exception as e:
        logger.error(f"Failed to create migrations table: {e}")
        raise


def record_migration(db: Database, name: str):
    """Record that a migration has been applied."""
    from datetime import datetime
    from sqlalchemy import text
    try:
        with db.get_session() as session:
            session.execute(
                text("INSERT OR IGNORE INTO migrations (name, applied_at) VALUES (:name, :applied_at)"),
                {"name": name, "applied_at": datetime.utcnow().isoformat()}
            )
            session.commit()
    except Exception as e:
        logger.error(f"Failed to record migration {name}: {e}")
        raise


def run_migrations(db: Database, dry_run: bool = False) -> Dict[str, Any]:
    """Run all pending migrations."""
    results = {
        "applied": [],
        "skipped": [],
        "errors": []
    }
    
    # Create migrations table if it doesn't exist
    create_migrations_table(db)
    
    # Get applied migrations
    applied = set(get_applied_migrations(db))
    
    # Get all migration files
    migration_files = get_migration_files()
    
    for migration_file in migration_files:
        migration_name = migration_file.stem
        
        if migration_name in applied:
            results["skipped"].append(migration_name)
            continue
        
        try:
            # Import the migration module
            module_name = f"scripts.python.migrations.{migration_name}"
            module = importlib.import_module(module_name)
            
            # Get the 'up' function
            if not hasattr(module, 'up'):
                results["errors"].append(f"{migration_name}: No 'up' function found")
                continue
            
            if dry_run:
                logger.info(f"[DRY RUN] Would apply migration: {migration_name}")
                results["applied"].append(migration_name)
            else:
                # Run the migration
                logger.info(f"Applying migration: {migration_name}")
                migration_result = module.up(db)
                
                if migration_result.get("errors"):
                    results["errors"].extend([
                        f"{migration_name}: {err}" for err in migration_result["errors"]
                    ])
                
                # Record the migration
                record_migration(db, migration_name)
                results["applied"].append(migration_name)
                logger.info(f"Migration {migration_name} applied successfully")
        
        except Exception as e:
            error_msg = f"{migration_name}: {str(e)}"
            logger.error(f"Migration failed: {error_msg}")
            results["errors"].append(error_msg)
    
    return results
