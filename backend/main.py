from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from binance.client import Client
import pandas as pd
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

@app.get("/get_top_coins")
async def get_top_coins():
    try:
        # Get symbol names
        symbol_names = get_symbol_names()
        
        # Get 24hr ticker for volume ranking
        tickers = client.get_ticker()
        
        # Filter and sort USDT pairs by volume
        usdt_pairs = [t for t in tickers if t['symbol'].endswith('USDT')]
        sorted_pairs = sorted(usdt_pairs, key=lambda x: float(x.get('volume', 0)), reverse=True)[:50]  # Get top 50
        
        result = []
        for pair in sorted_pairs:
            try:
                # Get current 4h candle data
                klines = client.get_klines(
                    symbol=pair['symbol'],
                    interval=Client.KLINE_INTERVAL_4HOUR,
                    limit=100  # Need 100 candles for MA(99)
                )
                
                if klines:
                    df = pd.DataFrame(klines, columns=[
                        'timestamp', 'open', 'high', 'low', 'close', 'volume',
                        'close_time', 'quote_volume', 'trades',
                        'taker_base', 'taker_quote', 'ignore'
                    ])
                    
                    # Convert price columns to numeric
                    for col in ['open', 'high', 'low', 'close']:
                        df[col] = pd.to_numeric(df[col])
                    
                    # Calculate Moving Averages
                    df['MA7'] = df['close'].rolling(window=7).mean()
                    df['MA25'] = df['close'].rolling(window=25).mean()
                    df['MA99'] = df['close'].rolling(window=99).mean()
                    
                    # Get latest 4h candle
                    latest = df.iloc[-1]
                    
                    # Calculate change percentage
                    prev_close = float(df.iloc[-2]['close'])
                    current_close = float(latest['close'])
                    change = ((current_close - prev_close) / prev_close) * 100
                    
                    # Get symbol name
                    symbol = pair['symbol']
                    name = symbol_names.get(symbol, '').upper()
                    
                    result.append({
                        'symbol': symbol,
                        'name': name,
                        'timestamp': pd.to_datetime(latest['timestamp'], unit='ms').strftime('%Y/%m/%d %H:%M'),
                        'open': float(latest['open']),
                        'high': float(latest['high']),
                        'low': float(latest['low']),
                        'close': float(latest['close']),
                        'change': change,
                        'ma7': float(latest['MA7']),
                        'ma25': float(latest['MA25']),
                        'ma99': float(latest['MA99'])
                    })
            except Exception as e:
                print(f"Error processing {pair['symbol']}: {str(e)}")
                continue
        
        return result
    except Exception as e:
        return {"error": str(e)}

@app.get("/health")
async def health_check():
    return {"status": "ok"} 