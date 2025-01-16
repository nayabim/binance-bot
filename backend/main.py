from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from binance.client import Client
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Binance client
client = Client()

# Available intervals from Binance
INTERVALS = {
    "1m": "1 minute",
    "3m": "3 minutes",
    "5m": "5 minutes",
    "15m": "15 minutes",
    "30m": "30 minutes",
    "1h": "1 hour",
    "2h": "2 hours",
    "4h": "4 hours",
    "6h": "6 hours",
    "8h": "8 hours",
    "12h": "12 hours",
    "1d": "1 day",
    "3d": "3 days",
    "1w": "1 week",
    "1M": "1 month"
}

@app.get("/get_intervals")
async def get_intervals():
    return INTERVALS

def safe_float(value):
    try:
        float_val = float(value)
        if np.isnan(float_val) or np.isinf(float_val):
            return 0.0
        return float_val
    except:
        return 0.0

@app.get("/get_top_coins")
async def get_top_coins(interval: str = "4h", start_time: int = None):
    try:
        # Get symbol names
        symbol_names = get_symbol_names()
        
        # Get 24hr ticker for volume ranking
        tickers = client.get_ticker()
        
        # Filter and sort USDT pairs by volume
        usdt_pairs = [t for t in tickers if t['symbol'].endswith('USDT')]
        sorted_pairs = sorted(usdt_pairs, key=lambda x: float(x.get('volume', 0)), reverse=True)[:50]
        
        result = []
        for pair in sorted_pairs:
            try:
                # Get candle data based on selected interval
                klines = client.get_klines(
                    symbol=pair['symbol'],
                    interval=interval,
                    startTime=start_time,
                    limit=100  # Need 100 candles for MA(99)
                )
                
                if klines:
                    df = pd.DataFrame(klines, columns=[
                        'timestamp', 'open', 'high', 'low', 'close', 'volume',
                        'close_time', 'quote_volume', 'trades',
                        'taker_base', 'taker_quote', 'ignore'
                    ])
                    
                    # Convert price columns to numeric and handle NaN/Inf values
                    for col in ['open', 'high', 'low', 'close']:
                        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
                    
                    # Calculate Moving Averages with NaN handling
                    df['MA7'] = df['close'].rolling(window=7).mean().fillna(0)
                    df['MA25'] = df['close'].rolling(window=25).mean().fillna(0)
                    df['MA99'] = df['close'].rolling(window=99).mean().fillna(0)
                    
                    # Get latest candle
                    latest = df.iloc[-1]
                    
                    # Calculate change percentage with safety checks
                    try:
                        prev_close = safe_float(df.iloc[-2]['close'])
                        current_close = safe_float(latest['close'])
                        if prev_close > 0:
                            change = ((current_close - prev_close) / prev_close) * 100
                        else:
                            change = 0.0
                    except:
                        change = 0.0
                    
                    # Get symbol name
                    symbol = pair['symbol']
                    name = symbol_names.get(symbol, '').upper()
                    
                    # Ensure all values are JSON serializable
                    result.append({
                        'symbol': symbol,
                        'name': name,
                        'timestamp': pd.to_datetime(latest['timestamp'], unit='ms').strftime('%Y/%m/%d %H:%M'),
                        'open': safe_float(latest['open']),
                        'high': safe_float(latest['high']),
                        'low': safe_float(latest['low']),
                        'close': safe_float(latest['close']),
                        'change': safe_float(change),
                        'ma7': safe_float(latest['MA7']),
                        'ma25': safe_float(latest['MA25']),
                        'ma99': safe_float(latest['MA99'])
                    })
            except Exception as e:
                print(f"Error processing {pair['symbol']}: {str(e)}")
                continue
        
        return result
    except Exception as e:
        return {"error": str(e)}

def get_symbol_names():
    try:
        exchange_info = client.get_exchange_info()
        symbol_names = {}
        for symbol in exchange_info['symbols']:
            if symbol['symbol'].endswith('USDT'):
                base_asset = symbol['baseAsset']
                symbol_names[symbol['symbol']] = base_asset
        return symbol_names
    except:
        return {}

@app.get("/health")
async def health_check():
    return {"status": "ok"} 