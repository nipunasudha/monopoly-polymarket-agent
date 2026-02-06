# Database Setup Guide

## Quick Answer

**Q: Why do I have a `monopoly_agents.db` file?**

**A:** It's the SQLite database file created automatically when the FastAPI server starts. It stores forecasts, trades, and portfolio data.

**Q: Should it be in version control?**

**A:** **NO!** It's now properly ignored in `.gitignore`. Database files should never be committed.

## What Happened

When you run the server (`uvicorn scripts.python.server:app`), it automatically:
1. Creates a SQLite database file: `agents/monopoly_agents.db`
2. Creates the database tables (forecasts, trades, portfolio_snapshots)

This is normal behavior for the persistence layer implemented in Phase 2.1.

## Git Ignore Status

✅ **Fixed!** The database file is now ignored:

```gitignore
# SQLite database files
*.db
*.db-journal
*.db-wal
*.db-shm
monopoly_agents.db
```

## Database File Details

- **Location**: `agents/monopoly_agents.db`
- **Type**: SQLite 3 database
- **Size**: ~24KB (empty/minimal data)
- **Purpose**: Store forecasts, trades, and portfolio snapshots
- **Git Status**: Ignored (not tracked)

## What's Stored

The database contains three tables:

1. **forecasts** - AI predictions for markets
2. **trades** - Trade execution records
3. **portfolio_snapshots** - Portfolio state over time

## Safe to Delete?

**Yes!** You can safely delete the database file:

```bash
rm agents/monopoly_agents.db
```

It will be automatically recreated (empty) the next time you:
- Start the FastAPI server
- Run the application

## For Development

The database file is useful for:
- Testing the API endpoints
- Viewing stored forecasts/trades
- Debugging persistence logic

## For Testing

Tests use an **in-memory database** (`sqlite:///:memory:`), so they:
- Don't create any files
- Run faster
- Are completely isolated

## For Production

For production deployment, consider:
- Using PostgreSQL or MySQL instead of SQLite
- Storing the database file in a persistent volume
- Setting up regular backups
- Using environment variables for database URL

## More Information

See `agents/DATABASE.md` for detailed documentation about:
- Database schema
- Configuration options
- Backup procedures
- Migration strategies

## Summary

✅ Database file is **normal** - created by the application
✅ Database file is **ignored** - won't be committed to git  
✅ Database file is **safe to delete** - will be recreated
✅ Tests use **in-memory** - no file pollution

No action needed! The database setup is working correctly.
