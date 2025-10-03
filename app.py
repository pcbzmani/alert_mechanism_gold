import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
from exa_py import Exa
import requests
import numpy as np

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="Gold & Silver Alert System",
    page_icon="💰",
    layout="wide"
)

# Initialize session state
if 'alerts' not in st.session_state:
    st.session_state.alerts = []

# Initialize Exa client
@st.cache_resource
def init_exa_client():
    api_key = os.getenv('EXA_API_KEY')
    if not api_key:
        st.warning("⚠️ EXA_API_KEY not found. Using mock data for prices.")
        return None
    return Exa(api_key)

def get_usd_inr_exchange_rate():
    """Fetch USD to INR exchange rate using ExchangeRate-API"""
    try:
        api_key = os.getenv('EXCHANGERATE_API_KEY')
        if not api_key:
            st.warning("⚠️ EXCHANGERATE_API_KEY not found. Using fallback USD/INR rate of 83.5.")
            return 83.5
        
        url = f"https://v6.exchangerate-api.com/v6/{api_key}/latest/USD"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            return data['conversion_rates']['INR']
        else:
            st.warning(f"ExchangeRate-API returned status {response.status_code}. Using fallback rate.")
            return 83.5
    except Exception as e:
        st.warning(f"ExchangeRate-API Error: {str(e)}. Using fallback USD/INR rate of 83.5.")
        return 83.5

def get_current_price_exa(metal="gold", currency="USD"):
    """Fetch current prices using Exa API"""
    try:
        exa = init_exa_client()
        if not exa:
            return None
        
        currency_str = "USD" if currency == "USD" else "INR"
        query = f"current {metal} price {currency_str} per ounce today {datetime.now().year}"
        results = exa.search(query, num_results=5, use_autoprompt=True)
        
        sources = []
        for result in results.results:
            sources.append({
                'title': result.title,
                'url': result.url,
                'published': getattr(result, 'published_date', None)
            })
        
        return sources
    except Exception as e:
        st.error(f"Exa API Error: {str(e)}")
        return None

def get_historical_data(metal="gold", currency="USD"):
    """Fetch historical data for 4 days using MetalpriceAPI"""
    try:
        api_key = os.getenv('METALPRICEAPI_KEY')
        if not api_key:
            st.info("ℹ️ METALPRICEAPI_KEY not found. Using mock historical data.")
            return generate_mock_data(metal, currency)
        
        url = "https://api.metalpriceapi.com/v1/timeframe"
        
        days = 4  # Fixed to 4 days for free tier
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        end_date = datetime.now().strftime('%Y-%m-%d')
        
        symbol = "XAU" if metal.lower() == "gold" else "XAG"
        
        params = {
            "api_key": api_key,
            "start_date": start_date,
            "end_date": end_date,
            "base": "USD",
            "currencies": symbol
        }
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if not data.get('success'):
                raise ValueError("API response unsuccessful")
            
            dates = sorted(data['rates'].keys())
            prices = []
            for date in dates:
                usd_symbol = f"USD{symbol}"
                if usd_symbol in data['rates'][date]:
                    prices.append(data['rates'][date][usd_symbol])
                else:
                    inverse = data['rates'][date].get(symbol, 0)
                    if inverse > 0:
                        prices.append(1 / inverse)
                    else:
                        prices.append(None)
            
            valid_data = [(d, p) for d, p in zip(dates, prices) if p is not None]
            if not valid_data:
                raise ValueError("No valid price data found")
            
            dates, prices = zip(*valid_data)
            prices = list(prices)
            
            # Convert to INR if selected
            if currency == "INR":
                exchange_rate = get_usd_inr_exchange_rate()
                prices = [p * exchange_rate for p in prices]
            
            highs = [p * 1.015 for p in prices]
            lows = [p * 0.985 for p in prices]
            
            return {
                'date': list(dates),
                'price': prices,
                'high': highs,
                'low': lows
            }
        else:
            st.warning(f"MetalpriceAPI returned status {response.status_code}. Using mock data.")
            return generate_mock_data(metal, currency)
            
    except Exception as e:
        st.warning(f"MetalpriceAPI Error: {str(e)}. Using mock data.")
        return generate_mock_data(metal, currency)

def get_insights_from_cerebras(query, metal, stats):
    """Fetch AI insights using Cerebras SDK with dynamic import"""
    api_key = os.getenv("CEREBRAS_API_KEY")
    if not api_key:
        return "⚠️ CEREBRAS_API_KEY not found. Cannot generate insights."
    
    try:
        from cerebras.cloud.sdk import Cerebras
        client = Cerebras(api_key=api_key)
        response = client.chat.completions.create(
            messages=[{"role": "user", "content": query}],
            model="llama-4-scout-17b-16e-instruct",
        )
        if not hasattr(response, 'choices') or not response.choices:
            return "Error: Invalid response structure from Cerebras API."
        return response.choices[0].message.content
    except NameError as ne:
        if "pydantic" in str(ne).lower():
            st.warning("Pydantic issue detected in Cerebras SDK. Using mock insights.")
            return f"Mock analysis: The {metal} market shows a {stats['change_pct']:+.2f}% change over 4 days, likely influenced by macroeconomic factors and supply-demand dynamics."
        return f"NameError: {str(ne)}"
    except Exception as e:
        return f"Error querying Cerebras: {str(e)}"

def generate_mock_data(metal="gold", currency="USD"):
    """Generate mock data for 4 days"""
    base_prices = {"gold": 2050, "silver": 24.5}
    days = 4  # Fixed to 4 days
    
    base_price = base_prices.get(metal.lower(), 2050)
    
    if currency == "INR":
        base_price *= 83.5  # Fallback exchange rate
    
    dates = [(datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d') 
             for i in range(days, 0, -1)]
    
    np.random.seed(42)
    prices = base_price + np.cumsum(np.random.randn(days) * (base_price * 0.01))
    
    return {
        'date': dates,
        'price': prices.tolist(),
        'high': (prices * 1.015).tolist(),
        'low': (prices * 0.985).tolist()
    }

def calculate_stats(data):
    """Calculate price statistics"""
    df = pd.DataFrame(data)
    
    return {
        'current': df['price'].iloc[-1],
        'low': df['price'].min(),
        'high': df['price'].max(),
        'avg': df['price'].mean(),
        'change': df['price'].iloc[-1] - df['price'].iloc[0],
        'change_pct': ((df['price'].iloc[-1] - df['price'].iloc[0]) / df['price'].iloc[0]) * 100 if df['price'].iloc[0] != 0 else 0,
        'volatility': df['price'].std()
    }

def get_trend(change_pct):
    """Determine price trend"""
    if change_pct > 2:
        return "📈 Strong Upward", "green"
    elif change_pct > 0.5:
        return "↗️ Upward", "lightgreen"
    elif change_pct < -2:
        return "📉 Strong Downward", "red"
    elif change_pct < -0.5:
        return "↘️ Downward", "lightcoral"
    else:
        return "➡️ Stable", "gray"

def create_chart(data, metal, currency):
    """Create interactive price chart"""
    df = pd.DataFrame(data)
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=df['date'],
        y=df['price'],
        name='Price',
        line=dict(
            color='gold' if metal.lower() == 'gold' else 'silver',
            width=3
        ),
        mode='lines+markers',
        marker=dict(size=6),
        hovertemplate='<b>Date</b>: %{x}<br><b>Price</b>: ' + ('₹' if currency == "INR" else '$') + '%{y:.2f}<extra></extra>'
    ))
    
    df['ma'] = df['price'].rolling(window=min(4, len(df))).mean()
    fig.add_trace(go.Scatter(
        x=df['date'],
        y=df['ma'],
        name='Moving Average',
        line=dict(color='blue', width=2, dash='dot'),
        hovertemplate='<b>MA</b>: ' + ('₹' if currency == 'INR' else '$') + '%{y:.2f}<extra></extra>'
    ))
    
    fig.add_trace(go.Scatter(
        x=df['date'],
        y=df['high'],
        name='High',
        line=dict(color='rgba(0,255,0,0.3)', width=1),
        showlegend=False,
        hoverinfo='skip'
    ))
    
    fig.add_trace(go.Scatter(
        x=df['date'],
        y=df['low'],
        name='Low',
        fill='tonexty',
        fillcolor='rgba(0,100,80,0.1)',
        line=dict(color='rgba(255,0,0,0.3)', width=1),
        showlegend=False,
        hoverinfo='skip'
    ))
    
    fig.update_layout(
        title=f'{metal} Price Trend (4 Days, {currency})',
        xaxis_title='Date',
        yaxis_title=f'Price ({currency})',
        height=500,
        hovermode='x unified',
        template='plotly_white'
    )
    
    return fig

def check_alerts(metal, stats, threshold, alert_type):
    """Check if alerts should trigger"""
    if alert_type == "Price Drop" and stats['change_pct'] <= -threshold:
        return True, "drop"
    elif alert_type == "Price Rise" and stats['change_pct'] >= threshold:
        return True, "rise"
    elif alert_type == "Both":
        if stats['change_pct'] <= -threshold:
            return True, "drop"
        elif stats['change_pct'] >= threshold:
            return True, "rise"
    return False, None

# Main UI
st.title("💰 Gold & Silver Price Alert System")
st.caption("Real-time monitoring with Exa, MetalpriceAPI, and Cerebras APIs")

# Sidebar
with st.sidebar:
    st.header("⚙️ Settings")
    
    metal = st.selectbox(
        "Select Metal",
        ["Gold", "Silver"],
        format_func=lambda x: f"🥇 {x}" if x == "Gold" else f"🥈 {x}"
    )
    
    currency = st.selectbox(
        "Currency",
        ["USD", "INR"],
        format_func=lambda x: f"💵 {x}"
    )
    
    st.markdown("---")
    
    st.subheader("🔔 Price Alerts")
    alert_enabled = st.checkbox("Enable Alerts", value=True)
    
    if alert_enabled:
        alert_type = st.radio(
            "Alert When Price",
            ["Price Drop", "Price Rise", "Both"]
        )
        
        threshold = st.slider(
            "Threshold (%)",
            min_value=1.0,
            max_value=10.0,
            value=5.0,
            step=0.5
        )
    
    st.markdown("---")
    
    st.subheader("🔌 API Status")
    exa_status = "✅" if os.getenv('EXA_API_KEY') else "❌"
    metalprice_status = "✅" if os.getenv('METALPRICEAPI_KEY') else "❌"
    cerebras_status = "✅" if os.getenv('CEREBRAS_API_KEY') else "❌"
    exchangerate_status = "✅" if os.getenv('EXCHANGERATE_API_KEY') else "❌"
    
    st.caption(f"{exa_status} Exa API")
    st.caption(f"{metalprice_status} MetalpriceAPI (Historical)")
    st.caption(f"{cerebras_status} Cerebras API (Insights)")
    st.caption(f"{exchangerate_status} ExchangeRate-API (USD/INR)")
    
    st.markdown("---")
    
    if st.button("🔄 Refresh Data", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# Main content
tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "📰 News Sources", "ℹ️ About"])

with tab1:
    st.subheader(f"📈 {metal} Price Analysis - 4 Days ({currency})")
    
    with st.spinner("Fetching data..."):
        data = get_historical_data(metal.lower(), currency)
        
        if data and len(data['price']) > 0:
            stats = calculate_stats(data)
            trend_text, trend_color = get_trend(stats['change_pct'])
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    "💵 Current Price",
                    f"{'₹' if currency == 'INR' else '$'}{stats['current']:.2f}",
                    f"{'₹' if currency == 'INR' else '$'}{stats['change']:+.2f} ({stats['change_pct']:+.2f}%)"
                )
            
            with col2:
                st.metric(
                    "📉 Period Low",
                    f"{'₹' if currency == 'INR' else '$'}{stats['low']:.2f}"
                )
            
            with col3:
                st.metric(
                    "📈 Period High",
                    f"{'₹' if currency == 'INR' else '$'}{stats['high']:.2f}"
                )
            
            with col4:
                st.metric(
                    "📊 Average",
                    f"{'₹' if currency == 'INR' else '$'}{stats['avg']:.2f}"
                )
            
            st.markdown(f"### Market Trend: :{trend_color}[{trend_text}] ({stats['change_pct']:+.2f}%)")
            
            price_position = (stats['current'] - stats['low']) / (stats['high'] - stats['low']) if stats['high'] != stats['low'] else 0
            st.progress(price_position, text=f"Price Position: {price_position*100:.1f}% of range")
            
            if alert_enabled:
                alert_triggered, alert_direction = check_alerts(
                    metal, stats, threshold, alert_type
                )
                
                if alert_triggered:
                    if alert_direction == "drop":
                        st.error(f"🚨 **ALERT**: {metal} price dropped by {abs(stats['change_pct']):.2f}%!")
                    else:
                        st.success(f"🚀 **ALERT**: {metal} price rose by {stats['change_pct']:.2f}%!")
            
            st.markdown("---")
            
            fig = create_chart(data, metal, currency)
            st.plotly_chart(fig, use_container_width=True)
            
            st.subheader("🤖 AI Market Insights (Powered by Cerebras)")
            insight_query = f"Provide a brief analysis of the current {metal} market based on this data: Current price {'₹' if currency == 'INR' else '$'}{stats['current']:.2f}, 4-day change {stats['change_pct']:+.2f}%, high {'₹' if currency == 'INR' else '$'}{stats['high']:.2f}, low {'₹' if currency == 'INR' else '$'}{stats['low']:.2f}. What might be influencing the price?"
            with st.spinner("Generating insights..."):
                insights = get_insights_from_cerebras(insight_query, metal, stats)
            st.markdown(insights)
            
            st.subheader("📋 Detailed Statistics")
            
            col_table1, col_table2 = st.columns(2)
            
            with col_table1:
                stats_df = pd.DataFrame({
                    'Metric': ['Current Price', 'Lowest Price', 'Highest Price'],
                    'Value': [
                        f"{'₹' if currency == 'INR' else '$'}{stats['current']:.2f}",
                        f"{'₹' if currency == 'INR' else '$'}{stats['low']:.2f}",
                        f"{'₹' if currency == 'INR' else '$'}{stats['high']:.2f}"
                    ]
                })
                st.dataframe(stats_df, hide_index=True, use_container_width=True)
            
            with col_table2:
                stats_df2 = pd.DataFrame({
                    'Metric': ['Average Price', 'Volatility', 'Price Change'],
                    'Value': [
                        f"{'₹' if currency == 'INR' else '$'}{stats['avg']:.2f}",
                        f"{'₹' if currency == 'INR' else '$'}{stats['volatility']:.2f}",
                        f"{'₹' if currency == 'INR' else '$'}{stats['change']:+.2f} ({stats['change_pct']:+.2f}%)"
                    ]
                })
                st.dataframe(stats_df2, hide_index=True, use_container_width=True)
        else:
            st.error("Unable to fetch data. Please check your API configuration.")

with tab2:
    st.subheader(f"📰 Latest {metal} Price Sources ({currency})")
    
    with st.spinner("Searching latest sources..."):
        sources = get_current_price_exa(metal.lower(), currency)
        
        if sources:
            st.success(f"Found {len(sources)} sources")
            
            for idx, source in enumerate(sources, 1):
                with st.container():
                    col1, col2 = st.columns([5, 1])
                    
                    with col1:
                        st.markdown(f"**{idx}. {source['title']}**")
                        if source['published']:
                            st.caption(f"📅 {source['published']}")
                        else:
                            st.caption("📅 Date not available")
                    
                    with col2:
                        st.link_button("🔗 Visit", source['url'], use_container_width=True)
                    
                    st.markdown("---")
        else:
            st.warning("⚠️ Unable to fetch sources. Please check Exa API configuration.")
            
            with st.expander("ℹ️ How to fix this"):
                st.markdown("""
                1. Get your Exa API key from: https://exa.ai
                2. Add to `.env` file:
                   ```
                   EXA_API_KEY=your_api_key_here
                   ```
                3. Restart the application
                """)

with tab3:
    st.subheader("ℹ️ About This System")
    
    st.markdown("""
    ### 🎯 Features
    
    - **Real-time Price Monitoring**: Track gold and silver prices in USD or INR
    - **Historical Analysis**: View trends over 4 days (MetalpriceAPI free tier limit)
    - **Price Alerts**: Get notified when prices change significantly
    - **Interactive Charts**: Explore price movements with Plotly
    - **Latest Sources**: See current price sources from across the web
    - **AI Insights**: Get market analysis powered by Cerebras
    
    ### 🔌 API Integration
    
    This system uses four APIs:
    
    1. **Exa API** - For current price sources and news
       - Searches the web for latest price information
       - Provides multiple sources for verification
    
    2. **MetalpriceAPI** - For historical price data
       - Fetches 4 days of data in free tier
       - Sign up at https://metalpriceapi.com for a free API key
    
    3. **Cerebras API** - For AI-powered market insights
       - Uses LLM to analyze trends and provide commentary
       - Note: If Cerebras API fails, mock insights are provided
    
    4. **ExchangeRate-API** - For USD to INR conversion
       - Converts USD prices to INR
       - Sign up at https://www.exchangerate-api.com for a free API key
    
    ### 📊 Understanding Trends
    
    - 📈 **Strong Upward**: Price increased by more than 2%
    - ↗️ **Upward**: Price increased by 0.5% to 2%
    - ➡️ **Stable**: Price changed by -0.5% to 0.5%
    - ↘️ **Downward**: Price decreased by 0.5% to 2%
    - 📉 **Strong Downward**: Price decreased by more than 2%
    
    ### 🔔 Setting Up Alerts
    
    1. Enable alerts in the sidebar
    2. Choose alert type (drop, rise, or both)
    3. Set your threshold percentage
    4. Alerts will show on the dashboard when triggered
    
    ### ⚙️ Configuration
    
    Create a `.env` file with your API keys:
    
    ```
    EXA_API_KEY=your_exa_api_key
    METALPRICEAPI_KEY=your_metalpriceapi_key
    CEREBRAS_API_KEY=your_cerebras_api_key
    EXCHANGERATE_API_KEY=your_exchangerate_api_key
    ```
    
    ### ⚠️ Important Disclaimer
    
    - This tool is for **informational purposes only**
    - Always verify prices with official sources
    - Not financial advice
    - Consult professionals before trading
    - Note: High/low prices are approximated in free API tier.
    """)

# Footer
st.markdown("---")
col1, col2, col3 = st.columns(3)

with col1:
    data_source = "Live APIs" if (os.getenv('EXA_API_KEY') and os.getenv('METALPRICEAPI_KEY') and os.getenv('CEREBRAS_API_KEY') and os.getenv('EXCHANGERATE_API_KEY')) else "Mock Data"
    st.caption(f"🔌 Data Source: {data_source}")

with col2:
    st.caption(f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

with col3:
    st.caption("💻 Built with Streamlit")
    