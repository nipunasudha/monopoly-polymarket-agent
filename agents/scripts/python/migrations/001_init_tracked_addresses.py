"""
Migration: Initialize tracked addresses from fixture.

This migration loads the default tracked addresses from the fixture file
and adds them to the database if they don't already exist.
"""
import json
from pathlib import Path
from agents.connectors.database import Database


def up(db: Database) -> dict:
    """Run the migration."""
    results = {
        "added": 0,
        "skipped": 0,
        "errors": []
    }
    
    try:
        # Find fixture file relative to this migration file
        migration_dir = Path(__file__).parent
        fixture_path = migration_dir.parent.parent.parent / "tests" / "fixtures" / "tracked_addresses.json"
        
        if not fixture_path.exists():
            results["errors"].append(f"Fixture file not found: {fixture_path}")
            return results
        
        with open(fixture_path, 'r') as f:
            default_addresses = json.load(f)
        
        for addr_data in default_addresses:
            try:
                db.add_tracked_address(addr_data["address"], addr_data.get("name"))
                results["added"] += 1
            except ValueError:
                # Address already exists, skip
                results["skipped"] += 1
            except Exception as e:
                results["errors"].append(f"Failed to add {addr_data.get('address', 'unknown')}: {str(e)}")
        
    except Exception as e:
        results["errors"].append(f"Migration failed: {str(e)}")
    
    return results


def down(db: Database) -> dict:
    """Rollback the migration (remove all tracked addresses)."""
    results = {
        "removed": 0,
        "errors": []
    }
    
    try:
        addresses = db.get_tracked_addresses()
        for addr in addresses:
            try:
                db.delete_tracked_address(addr.address)
                results["removed"] += 1
            except Exception as e:
                results["errors"].append(f"Failed to remove {addr.address}: {str(e)}")
    except Exception as e:
        results["errors"].append(f"Rollback failed: {str(e)}")
    
    return results
