# Markets Page - Next.js Implementation

## Overview
The Markets page displays available Polymarket prediction markets with full support for fixture data in dry_run mode.

## Features

### 🎯 Smart Data Loading
- **Dry Run Mode**: Instantly loads 8 realistic fixture markets (no API calls)
- **Live Mode**: Fetches real markets from Polymarket API
- **Auto-detection**: Uses `TRADING_MODE` env var to determine mode

### 📊 Market Cards Display
Each market card shows:
- **Question** - The prediction market question
- **Status** - Active/Inactive badge
- **End Date** - When the market closes
- **Outcomes** - Yes/No with color-coded probabilities
- **Volume & Liquidity** - Trading metrics (when available)
- **Description** - Market resolution criteria

### 🎨 UI Features
- **Color-coded prices**:
  - Green (≥70%): High probability
  - Yellow (50-70%): Moderate probability  
  - Red (<50%): Low probability
- **Stats bar**: Total markets, active count, total volume
- **Fixture data indicator**: Yellow badge when using mock data
- **Refresh button**: Reload markets on demand
- **Responsive grid**: Adapts to screen size
- **Hover effects**: Cards lift on hover

## API Endpoint

### GET `/api/markets`

**Response (Dry Run):**
```json
{
  "markets": [
    {
      "id": "mock_id",
      "question": "Will Bitcoin reach $100,000 in 2025?",
      "end": "2025-12-31T23:59:59Z",
      "active": true,
      "outcomes": ["Yes", "No"],
      "outcome_prices": ["0.73", "0.27"],
      "description": "Resolves to 'Yes' if Bitcoin trades at or above $100,000",
      "volume": 3200000.0,
      "liquidity": 150000.0
    }
  ],
  "dry_run": true
}
```

**Response (Live):**
```json
{
  "markets": [...],
  "dry_run": false
}
```

## Fixture Data

### 8 Realistic Markets
1. **DOGE Federal Spending** - $200-250B cuts prediction
2. **Trump Approval** - Q1 2025 polling
3. **Bitcoin $100K** - Crypto milestone
4. **AGI Achievement** - AI breakthrough by 2026
5. **Fed Rate Cuts** - Below 4% in 2025
6. **SpaceX Mars Landing** - 2026 mission
7. **US Recession** - 2025 economic prediction
8. **AI Regulation** - US legislation in 2025

All fixture markets include:
- Realistic probabilities
- Trading volume ($380K - $3.2M)
- Liquidity pools ($19K - $150K)
- Proper resolution criteria

## Files Modified

### Backend
**`agents/scripts/python/server.py`**
- Added `/api/markets` endpoint
- Returns fixture data if `TRADING_MODE != "live"`
- Fetches real markets from Polymarket in live mode
- Includes volume and liquidity when available

### Frontend
**`monopoly-dashboard/app/markets/page.tsx`**
- Full React component with state management
- Loading, error, and empty states
- Formatted prices, volumes, dates
- Color-coded probability indicators
- Responsive card layout

**`monopoly-dashboard/lib/types.ts`**
- Added `MarketsResponse` interface
- Extended `Market` with volume/liquidity fields

**`monopoly-dashboard/lib/api.ts`**
- Added `marketsAPI.getAll()` function
- Type-safe API client

## Usage

### View Markets Page
```
http://localhost:3000/markets
```

### Fixture Data Mode (default)
The page automatically uses fixture data when backend is in dry_run mode:
```bash
# In agents/.env
TRADING_MODE=dry_run
```

You'll see:
- ⚡ Instant load (<100ms)
- 🟡 "Fixture Data" badge
- 8 realistic markets

### Live Data Mode
To fetch real Polymarket data:
```bash
# In agents/.env
TRADING_MODE=live
```

Requires:
- Polymarket API access
- Network connection
- May be slower (~2-5 seconds)

## Performance

### Dry Run Mode
- Load time: **<100ms**
- No API calls
- No rate limits
- Perfect for development

### Live Mode
- Load time: **2-5 seconds**
- Real Polymarket data
- Subject to API rate limits
- Production use

## UI States

### Loading
```
┌─────────────────────────────┐
│  Market Scanner             │
│                             │
│      [Spinning loader]      │
│   Loading markets...        │
└─────────────────────────────┘
```

### Error
```
┌─────────────────────────────┐
│  Market Scanner             │
│                             │
│      [Error icon]           │
│   Error Loading Markets     │
│   [Error message]           │
│   [Retry Button]            │
└─────────────────────────────┘
```

### Empty
```
┌─────────────────────────────┐
│  Market Scanner             │
│                             │
│      [Chart icon]           │
│   No Markets Available      │
└─────────────────────────────┘
```

### Loaded
```
┌──────────────────────────────────────┐
│  Market Scanner        [🟡 Fixture] │
│  Browse and analyze markets [Refresh]│
├──────────────────────────────────────┤
│  Total: 8  Active: 8  Volume: $8.3M │
├──────────────────────────────────────┤
│  ┌────────────────────────────────┐  │
│  │ Will Bitcoin reach $100,000?   │  │
│  │ Ends: Dec 31, 2025   [Active]  │  │
│  │                                 │  │
│  │ Yes: 73.0%  No: 27.0%          │  │
│  │ Volume: $3.2M  Liquidity: $150K│  │
│  └────────────────────────────────┘  │
│  [... more markets ...]             │
└──────────────────────────────────────┘
```

## Color Coding

### Probability Colors
- **Green** (≥70%): `text-green-600 bg-green-50`
- **Yellow** (50-69%): `text-yellow-600 bg-yellow-50`
- **Red** (<50%): `text-red-600 bg-red-50`

### Status Badges
- **Active**: Green badge
- **Inactive**: Gray badge
- **Fixture Data**: Yellow badge with info icon

## Format Functions

### Price
```typescript
formatPrice("0.73") → "73.0%"
```

### Volume
```typescript
formatVolume(3200000) → "$3.2M"
formatVolume(85000) → "$85K"
formatVolume(450) → "$450"
```

### Date
```typescript
formatDate("2025-12-31T23:59:59Z") → "Dec 31, 2025"
```

## Testing

### Test Fixture Data
```bash
# Ensure dry_run mode
cd agents
grep TRADING_MODE .env  # Should be 'dry_run'

# Start backend
uv run dev

# In another terminal, start frontend
cd monopoly-dashboard
npm run dev

# Visit http://localhost:3000/markets
# Should see 8 fixture markets instantly
```

### Test Live Data
```bash
# Switch to live mode
cd agents
echo "TRADING_MODE=live" > .env

# Restart backend
uv run dev

# Refresh markets page
# Should fetch real Polymarket data
```

### Test Error Handling
```bash
# Stop backend
# Visit markets page
# Should show error state with retry button
```

## Next Steps

This implementation provides:
- ✅ Full markets browsing
- ✅ Fixture data for fast development
- ✅ Live data support for production
- ✅ Beautiful, responsive UI
- ✅ Error handling
- ✅ Loading states

Future enhancements could include:
- 🔍 Search/filter markets
- 📈 Price history charts
- 🔔 Market alerts
- 💾 Favorite markets
- 📊 Advanced sorting
- 🎯 Market categories

---

**Note**: The markets page is now fully functional and matches the original Jinja2 template design with improved interactivity and fixture data support!
