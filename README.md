# Gold & Silver Price Alert System 💰

A comprehensive real-time price monitoring and alert system for gold and silver prices with historical trend analysis.

## Features

- 📊 Real-time price monitoring using Exa API
- 📈 Historical price comparison (week, month, year) using Cerbras API
- 🔔 Customizable price alerts
- 📉 Trend analysis with visual indicators
- 📰 Latest news integration
- 🎨 Interactive charts with Plotly
- 📧 Email notifications (optional)

## Architecture

```
├── app.py                 # Main Streamlit application
├── utils.py              # Helper functions (optional)
├── requirements.txt      # Python dependencies
├── .env                  # API keys (not in git)
├── .env.example         # Environment template
└── README.md            # This file
```

## Installation

### 1. Clone or Create Project Directory

```bash
mkdir gold-silver-alert
cd gold-silver-alert
```

### 2. Create Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Mac/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

Edit `.env` and add your API keys:

```
EXA_API_KEY=your_actual_exa_api_key
CERBRAS_API_KEY=your_actual_cerbras_api_key
```

#### Getting API Keys

**Exa API:**
1. Visit [https://exa.ai](https://exa.ai)
2. Sign up for an account
3. Navigate to API settings
4. Generate your API key

**Cerbras API:**
1. Visit Cerbras website
2. Create an account
3. Get your API key from the dashboard

## Usage

### Running the Application

```bash
streamlit run app.py
```

The application will open in your default browser at `http://localhost:8501`

### Features Guide

#### 1. Select Metal
- Choose between Gold or Silver from the sidebar

#### 2. Analysis Period
- **Week**: 7 days of historical data
- **Month**: 30 days of historical data
- **Year**: 365 days of historical data

#### 3. Price Alerts
- Enable/disable alerts
- Set alert type:
  - Price Drop: Alert when price decreases
  - Price Rise: Alert when price increases
  - Both: Alert for both scenarios
- Set threshold percentage (1-10%)

#### 4. Dashboard Metrics
- **Current Price**: Latest price with change indicator
- **Lowest Price**: Minimum price in selected period
- **Highest Price**: Maximum price in selected period
- **Average Price**: Mean price with volatility

#### 5. Trend Analysis
The system calculates trends based on price changes:
- 📈 Strong Upward: >2% increase
- ↗️ Upward: 0.5-2% increase
- ➡️ Stable: -0.5% to 0.5% change
- ↘️ Downward: -2% to -0.5% decrease
- 📉 Strong Downward: <-2% decrease

## API Integration Details

### Exa API Integration

The Exa API is used to search for current gold/silver prices from various sources across the web.

```python
exa = Exa(api_key)
results = exa.search(
    query=f"current {metal} price USD per ounce today",
    num_results=5,
    use_autoprompt=True
)
```

### Cerbras API Integration

The Cerbras API provides historical price data for comparison and trend analysis.

**Note:** If you don't have the Cerbras API yet, the system will use mock data for demonstration. Update the `get_historical_data_cerbras()` function with actual Cerbras API endpoints once available.

```python
# Example Cerbras API call (adjust based on actual API docs)
url = f"https://api.cerbras.com/v1/metals/{metal}/historical"
headers = {"Authorization": f"Bearer {api_key}"}
params = {"period": period, "currency": "USD"}
response = requests.get(url, headers=headers, params=params)
```

## Data Flow

```
User Input (Metal, Period)
        ↓
Exa API → Current Prices & News
        ↓
Cerbras API → Historical Data
        ↓
Analysis Engine → Statistics & Trends
        ↓
Visualization → Charts & Metrics
        ↓
Alert System → Notifications
```

## Customization

### Adding Email Alerts

1. Add SMTP configuration to `.env`:
```
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_EMAIL=your_email@gmail.com
SMTP_PASSWORD=your_app_password
```

2. Use the `send_email_alert()` function from `utils.py`

### Modifying Trend Calculations

Edit the `determine_trend()` function in `app.py` to adjust:
- Threshold percentages
- Trend categories
- Moving average windows

### Custom Visualizations

The `create_price_chart()` function uses Plotly. Modify it to add:
- Volume indicators
- Moving averages
- Bollinger Bands
- RSI indicators

## Troubleshooting

### API Key Issues
- Verify keys are correct in `.env`
- Check API key permissions and quotas
- Ensure no extra spaces in `.env` file

### Import Errors
```bash
pip install --upgrade -r requirements.txt
```

### Port Already in Use
```bash
streamlit run app.py --server.port 8502
```

### Mock Data Mode
If seeing mock data:
- Check Cerbras API key is correct
- Verify API endpoint URL
- Check network connectivity

## Performance Optimization

### Caching
The app uses Streamlit caching:
- `@st.cache_resource` for API clients
- `@st.cache_data` for data fetching

### Rate Limiting
Consider implementing rate limiting for API calls:
```python
import time
from functools import wraps

def rate_limit(calls_per_minute):
    def decorator(func):
        last_called = [0.0]
        @wraps(func)
        def wrapper(*args, **kwargs):
            elapsed = time.time() - last_called[0]
            if elapsed < 60 / calls_per_minute:
                time.sleep(60 / calls_per_minute - elapsed)
            result = func(*args, **kwargs)
            last_called[0] = time.time()
            return result
        return wrapper
    return decorator
```

## Future Enhancements

- [ ] Multi-user support with authentication
- [ ] Database integration for historical storage
- [ ] Mobile app version
- [ ] Webhook notifications (Telegram, Slack)
- [ ] Advanced technical indicators
- [ ] Portfolio tracking
- [ ] Multi-currency support
- [ ] Comparison with other commodities

## Contributing

Feel free to submit issues and enhancement requests!

## License

MIT License - feel free to use for personal or commercial projects.

## Support

For issues with:
- **Exa API**: Contact Exa support
- **Cerbras API**: Contact Cerbras support
- **Application**: Create an issue in the repository

## Disclaimer

⚠️ **Important**: This tool is for informational purposes only. Always verify prices with official sources before making any trading or investment decisions. Past performance does not guarantee future results.

---

Built with ❤️ using Streamlit, Plotly, and Python