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

@app.get("/get_top_coins")
async def get_top_coins():
    try:
        # Get 24hr ticker for all symbols
        tickers = client.get_ticker()
        
        # Filter USDT pairs and sort by volume
        usdt_pairs = [t for t in tickers if t['symbol'].endswith('USDT')]
        sorted_pairs = sorted(usdt_pairs, key=lambda x: float(x['volume']), reverse=True)[:10]
        
        result = []
        for pair in sorted_pairs:
            # Get 4h candles
            klines = client.get_klines(
                symbol=pair['symbol'],
                interval=Client.KLINE_INTERVAL_4HOUR,
                limit=100  # For MA calculations
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
                
                # Calculate MAs
                df['MA7'] = df['close'].rolling(window=7).mean()
                df['MA25'] = df['close'].rolling(window=25).mean()
                df['MA99'] = df['close'].rolling(window=99).mean()
                
                # Get latest candle
                latest = df.iloc[-1]
                prev_close = float(df.iloc[-2]['close'])
                current_close = float(latest['close'])
                
                # Calculate change percentage and amplitude
                change = ((current_close - prev_close) / prev_close) * 100
                amplitude = ((float(latest['high']) - float(latest['low'])) / float(latest['low'])) * 100
                
                # Format timestamp
                candle_time = pd.to_datetime(latest['timestamp'], unit='ms')
                
                result.append({
                    'symbol': pair['symbol'],
                    'timestamp': candle_time.strftime('%Y/%m/%d %H:%M'),
                    'open': float(latest['open']),
                    'high': float(latest['high']),
                    'low': float(latest['low']),
                    'close': float(latest['close']),
                    'change': change,
                    'amplitude': amplitude,
                    'ma7': float(latest['MA7']),
                    'ma25': float(latest['MA25']),
                    'ma99': float(latest['MA99'])
                })
        
        return result
        
    except Exception as e:
        return {"error": str(e)}

@app.get("/health")
async def health_check():
    return {"status": "ok"} 