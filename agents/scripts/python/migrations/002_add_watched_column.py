"""
Migration: Add watched column to tracked_addresses table.

This migration adds a 'watched' boolean column to track whether
the bot should follow each address's trade patterns.
"""
from sqlalchemy import text
from agents.connectors.database import Database


def up(db: Database) -> dict:
    """Run the migration."""
    results = {
        "added": 0,
        "errors": []
    }
    
    try:
        with db.get_session() as session:
            # Add watched column if it doesn't exist
            # SQLite doesn't support ALTER TABLE ADD COLUMN IF NOT EXISTS directly
            # So we'll use a try/except approach
            try:
                session.execute(text("ALTER TABLE tracked_addresses ADD COLUMN watched BOOLEAN DEFAULT 0"))
                session.commit()
                results["added"] = 1
            except Exception as e:
                # Column might already exist, check if it's a different error
                error_str = str(e).lower()
                if "duplicate column" in error_str or "already exists" in error_str:
                    # Column already exists, that's fine
                    pass
                else:
                    results["errors"].append(f"Failed to add watched column: {str(e)}")
    except Exception as e:
        results["errors"].append(f"Migration failed: {str(e)}")
    
    return results


def down(db: Database) -> dict:
    """Rollback the migration (remove watched column)."""
    results = {
        "removed": 0,
        "errors": []
    }
    
    try:
        with db.get_session() as session:
            # SQLite doesn't support DROP COLUMN easily, would need table recreation
            # For now, just set all watched to False
            session.execute(text("UPDATE tracked_addresses SET watched = 0"))
            session.commit()
            results["removed"] = 1
            results["errors"].append("Note: SQLite doesn't support DROP COLUMN. Set all watched to False instead.")
    except Exception as e:
        results["errors"].append(f"Rollback failed: {str(e)}")
    
    return results
