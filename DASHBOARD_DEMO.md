# Dashboard Demo Guide

## 🎨 Live Dashboard Now Available!

Phase 2.3 is complete with a beautiful, functional web dashboard.

## Quick Start

### 1. Start the Server
```bash
cd agents
uvicorn scripts.python.server:app --reload
```

### 2. Open Your Browser
```
http://localhost:8000
```

## 📱 Dashboard Pages

### Portfolio Overview (`/`)
**What you'll see:**
- Balance, Total Value, P&L, Win Rate cards
- Equity curve chart showing portfolio value over time
- Recent activity feed with latest trades
- Color-coded profit/loss indicators

**Features:**
- Real-time portfolio stats
- Visual chart with Chart.js
- Responsive design (mobile/desktop)

### Forecasts (`/forecasts`)
**What you'll see:**
- Forecast cards for each prediction
- Probability percentages with visual bars
- Confidence scores
- Full reasoning text
- Market details

**Features:**
- HTMX refresh button
- Probability distribution bars
- Clean card layout

### Trade History (`/trades`)
**What you'll see:**
- Table with all trades
- Status badges (executed, pending, failed)
- BUY/SELL indicators
- Market questions and outcomes
- Timestamps

**Features:**
- Sortable table
- Color-coded status
- Responsive on mobile

### Markets Scanner (`/markets`)
**Status:** Placeholder (coming in Phase 3)
- Will show active markets
- Edge estimation
- Filtering capabilities

## 🎯 Technology Stack

### Zero Build Step
- **Tailwind CSS** - Styling via CDN
- **HTMX** - Dynamic updates via CDN
- **Chart.js** - Charts via CDN
- **Alpine.js** - Interactivity via CDN

**No npm, no webpack, no build tools needed!**

### Backend
- **FastAPI** - Web framework
- **Jinja2** - Template engine
- **SQLite** - Database
- **Python** - 100% Python stack

## 🧪 Testing

All dashboard pages are fully tested:

```bash
# Run dashboard tests
uv run test-agents tests/integration/test_dashboard.py

# Results: 22 passed in 0.61s
```

**What's tested:**
- ✅ Page loading
- ✅ Data rendering
- ✅ Empty states
- ✅ Navigation
- ✅ Responsive design
- ✅ Asset loading
- ✅ Chart rendering

## 📊 Demo Workflow

### 1. Start with Empty Dashboard
```bash
# Start server
uvicorn scripts.python.server:app --reload

# Open http://localhost:8000
# You'll see empty states with helpful messages
```

### 2. Add Sample Data
```python
# In Python shell or script
from agents.connectors.database import Database

db = Database()

# Add a forecast
db.save_forecast({
    "market_id": "12345",
    "market_question": "Will Bitcoin reach $100k by end of 2026?",
    "outcome": "Yes",
    "probability": 0.35,
    "confidence": 0.70,
    "reasoning": "Based on historical trends and institutional adoption.",
})

# Add a trade
db.save_trade({
    "market_id": "12345",
    "market_question": "Will Bitcoin reach $100k by end of 2026?",
    "outcome": "Yes",
    "side": "BUY",
    "size": 250.0,
    "price": 0.45,
    "forecast_probability": 0.60,
    "status": "executed",
})

# Add portfolio snapshot
db.save_portfolio_snapshot({
    "balance": 1000.0,
    "total_value": 1250.0,
    "open_positions": 3,
    "total_pnl": 250.0,
    "win_rate": 0.65,
    "total_trades": 10,
})
```

### 3. Refresh Dashboard
- Refresh your browser
- See the data populate across all pages
- Watch the equity curve chart render
- View forecasts and trades

## 🎨 UI Features

### Responsive Design
- **Mobile**: Single column, stacked layout
- **Tablet**: 2-column grid
- **Desktop**: 4-column grid, full tables

### Color Coding
- **Green**: Profits, BUY orders, executed trades
- **Red**: Losses, SELL orders, failed trades
- **Yellow**: Pending trades
- **Indigo**: Primary actions and highlights

### Interactive Elements
- **HTMX**: Refresh buttons without page reload
- **Charts**: Interactive Chart.js visualizations
- **Hover**: Table row highlights
- **Links**: Smooth navigation

## 📁 File Structure

```
agents/
├── dashboard/
│   ├── templates/
│   │   ├── base.html          # 70 lines - Base layout
│   │   ├── portfolio.html     # 150 lines - Portfolio page
│   │   ├── forecasts.html     # 120 lines - Forecasts page
│   │   ├── trades.html        # 130 lines - Trades page
│   │   └── markets.html       # 40 lines - Markets placeholder
│   └── static/                # (empty - using CDN)
│
└── scripts/python/
    └── server.py              # 340 lines - Enhanced server
```

## 🔍 API vs Dashboard

### Dashboard Routes (HTML)
- `GET /` - Portfolio page
- `GET /markets` - Markets page
- `GET /trades` - Trades page
- `GET /forecasts` - Forecasts page

### API Routes (JSON)
- `GET /api` - API info
- `GET /api/forecasts` - JSON forecasts
- `GET /api/trades` - JSON trades
- `GET /api/portfolio` - JSON portfolio

Both work simultaneously!

## 🎓 Development Tips

### Adding New Pages
1. Create template in `dashboard/templates/`
2. Add route in `server.py`
3. Add tests in `test_dashboard.py`

### Styling
- Use Tailwind utility classes
- Check [Tailwind docs](https://tailwindcss.com/docs)
- No custom CSS needed

### Interactivity
- Use HTMX for AJAX: `hx-get="/api/endpoint"`
- Use Alpine.js for state: `x-data="{ open: false }"`

### Charts
- Use Chart.js
- See portfolio.html for example
- Pass data via Jinja2: `{{ data | tojson }}`

## 🐛 Troubleshooting

### Templates Not Found
```
jinja2.exceptions.TemplateNotFound: portfolio.html
```
**Solution**: Check that templates directory exists at `agents/dashboard/templates/`

### Styles Not Loading
**Solution**: Check internet connection (CDN dependencies)

### Data Not Showing
**Solution**: Add sample data to database (see Demo Workflow above)

## 📊 Current Status

| Component | Status | Tests |
|-----------|--------|-------|
| Portfolio page | ✅ Complete | 7 |
| Forecasts page | ✅ Complete | 4 |
| Trades page | ✅ Complete | 4 |
| Markets page | 🚧 Placeholder | 1 |
| Navigation | ✅ Complete | 2 |
| Charts | ✅ Complete | 2 |
| Responsive | ✅ Complete | 2 |

## 🎉 Success!

- **153 tests passing**
- **4 dashboard pages**
- **Zero build step**
- **Beautiful UI**
- **Fast & responsive**

Ready for Phase 2.4 (Background Runner)!
