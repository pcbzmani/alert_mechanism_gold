"""

Utility functions for the Gold & Silver Alert System
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import json
import os

def send_email_alert(to_email, subject, body, smtp_config=None):
    """
    Send email alert when price thresholds are met
    
    Args:
        to_email: Recipient email address
        subject: Email subject
        body: Email body content
        smtp_config: Dictionary with SMTP configuration
    """
    try:
        if smtp_config is None:
            smtp_config = {
                'server': os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
                'port': int(os.getenv('SMTP_PORT', 587)),
                'email': os.getenv('SMTP_EMAIL'),
                'password': os.getenv('SMTP_PASSWORD')
            }
        
        msg = MIMEMultipart()
        msg['From'] = smtp_config['email']
        msg['To'] = to_email
        msg['Subject'] = subject
        
        msg.attach(MIMEText(body, 'html'))
        
        server = smtplib.SMTP(smtp_config['server'], smtp_config['port'])
        server.starttls()
        server.login(smtp_config['email'], smtp_config['password'])
        server.send_message(msg)
        server.quit()
        
        return True
    except Exception as e:
        print(f"Error sending email: {str(e)}")
        return False

def save_alert_history(metal, price, alert_type, timestamp):
    """Save alert history to JSON file"""
    try:
        history_file = 'alert_history.json'
        
        if os.path.exists(history_file):
            with open(history_file, 'r') as f:
                history = json.load(f)
        else:
            history = []
        
        history.append({
            'metal': metal,
            'price': price,
            'alert_type': alert_type,
            'timestamp': timestamp
        })
        
        with open(history_file, 'w') as f:
            json.dump(history, f, indent=2)
        
        return True
    except Exception as e:
        print(f"Error saving alert history: {str(e)}")
        return False

def load_alert_history():
    """Load alert history from JSON file"""
    try:
        history_file = 'alert_history.json'
        
        if os.path.exists(history_file):
            with open(history_file, 'r') as f:
                return json.load(f)
        return []
    except Exception as e:
        print(f"Error loading alert history: {str(e)}")
        return []

def calculate_rsi(prices, period=14):
    """
    Calculate Relative Strength Index (RSI)
    
    Args:
        prices: List of prices
        period: RSI period (default 14)
    
    Returns:
        RSI value
    """
    if len(prices) < period + 1:
        return None
    
    deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
    
    gains = [d if d > 0 else 0 for d in deltas]
    losses = [-d if d < 0 else 0 for d in deltas]
    
    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period
    
    if avg_loss == 0:
        return 100
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    
    return rsi

def format_price_alert_email(metal, current_price, change_pct, trend):
    """Format HTML email for price alerts"""
    html = f"""
    <html>
        <body style="font-family: Arial, sans-serif;">
            <h2 style="color: #FFD700;">🔔 {metal.title()} Price Alert</h2>
            <p>A significant price change has been detected:</p>
            <table style="border-collapse: collapse; width: 100%;">
                <tr>
                    <td style="padding: 8px; border: 1px solid #ddd;"><strong>Metal:</strong></td>
                    <td style="padding: 8px; border: 1px solid #ddd;">{metal.title()}</td>
                </tr>
                <tr>
                    <td style="padding: 8px; border: 1px solid #ddd;"><strong>Current Price:</strong></td>
                    <td style="padding: 8px; border: 1px solid #ddd;">${current_price:.2f}</td>
                </tr>
                <tr>
                    <td style="padding: 8px; border: 1px solid #ddd;"><strong>Change:</strong></td>
                    <td style="padding: 8px; border: 1px solid #ddd; color: {'green' if change_pct > 0 else 'red'};">
                        {change_pct:+.2f}%
                    </td>
                </tr>
                <tr>
                    <td style="padding: 8px; border: 1px solid #ddd;"><strong>Trend:</strong></td>
                    <td style="padding: 8px; border: 1px solid #ddd;">{trend}</td>
                </tr>
            </table>
            <p style="margin-top: 20px; color: #666;">
                This is an automated alert from your Gold & Silver Price Monitoring System.
            </p>
        </body>
    </html>
    """
    return html