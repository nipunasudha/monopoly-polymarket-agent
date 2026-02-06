# Database Information

## SQLite Database File

The application uses SQLite for local persistence. The database file is created automatically when the server starts.

### Default Location
```
agents/monopoly_agents.db
```

### Important Notes

⚠️ **The database file is NOT tracked in version control**

- The `.db` file is automatically ignored by git (see `.gitignore`)
- Each environment (dev, test, production) should have its own database
- Database files contain runtime data, not source code

### Database Schema

The database contains three main tables:

1. **forecasts** - Stores AI-generated market forecasts
   - market_id, probability, confidence, reasoning, etc.

2. **trades** - Stores trade execution records
   - market_id, side, size, status, transaction_hash, etc.

3. **portfolio_snapshots** - Stores portfolio state over time
   - balance, total_value, pnl, win_rate, etc.

### Configuration

To use a different database location, modify the initialization in `scripts/python/server.py`:

```python
# Use a different file
db = Database("sqlite:///path/to/your/database.db")

# Use in-memory database (for testing)
db = Database("sqlite:///:memory:")

# Use PostgreSQL (requires psycopg2)
db = Database("postgresql://user:pass@localhost/dbname")
```

### Testing

Tests use an in-memory database by default:
```python
test_db = Database("sqlite:///:memory:")
```

This ensures:
- Fast test execution
- No file system pollution
- Complete isolation between tests

### Backup

To backup your database:
```bash
# Simple copy
cp agents/monopoly_agents.db agents/monopoly_agents.backup.db

# SQLite dump
sqlite3 agents/monopoly_agents.db .dump > backup.sql
```

### Reset Database

To start fresh:
```bash
# Delete the database file
rm agents/monopoly_agents.db

# It will be recreated on next server start
```

Or programmatically:
```python
db.drop_tables()  # Remove all tables
db.create_tables()  # Recreate empty tables
```

### Migration

The database schema is created automatically via SQLAlchemy's `create_all()`. For production, consider using a migration tool like Alembic for schema changes.

### Size Considerations

SQLite is suitable for:
- ✅ Development and testing
- ✅ Single-user applications
- ✅ Moderate data volumes (< 1GB)
- ✅ Read-heavy workloads

For production with high volume:
- Consider PostgreSQL or MySQL
- The code supports any SQLAlchemy-compatible database
- Just change the connection string
