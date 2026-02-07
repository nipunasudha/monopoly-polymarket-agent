#!/usr/bin/env python
"""
Standalone script to run database migrations.
"""
import sys
from pathlib import Path

# Add agents directory to path (run from agents/ directory)
agents_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(agents_dir))

from agents.connectors.database import Database
from scripts.python.migrations.runner import run_migrations
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    db = Database()
    db.create_tables()
    
    print("Running database migrations...")
    results = run_migrations(db, dry_run=False)
    
    if results["applied"]:
        print(f"\n✓ Applied {len(results['applied'])} migrations:")
        for name in results["applied"]:
            print(f"  - {name}")
    
    if results["skipped"]:
        print(f"\n⊘ Skipped {len(results['skipped'])} migrations (already applied):")
        for name in results["skipped"]:
            print(f"  - {name}")
    
    if results["errors"]:
        print(f"\n✗ Errors:")
        for error in results["errors"]:
            print(f"  - {error}")
        sys.exit(1)
    
    if not results["applied"] and not results["errors"]:
        print("\n✓ No migrations to apply")
    
    print("\nMigration complete!")
