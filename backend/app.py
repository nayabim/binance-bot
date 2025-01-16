import asyncio
import websockets
import json
from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class BinanceDataStream:
    def __init__(self):
        self.ws_url = "wss://data-stream.binance.vision/ws"
        self.cached_data = {}
        
    async def connect_websocket(self):
        async with websockets.connect(self.ws_url) as websocket:
            # Subscribe to miniTicker stream for all symbols
            subscribe_message = {
                "method": "SUBSCRIBE",
                "params": ["!miniTicker@arr"],
                "id": 1
            }
            await websocket.send(json.dumps(subscribe_message))
            
            while True:
                try:
                    message = await websocket.recv()
                    data = json.loads(message)
                    
                    # Update cached data
                    if isinstance(data, list):  # miniTicker data comes as an array
                        for ticker in data:
                            symbol = ticker['s']
                            self.cached_data[symbol] = {
                                'symbol': symbol,
                                'open': float(ticker['o']),
                                'high': float(ticker['h']),
                                'low': float(ticker['l']),
                                'close': float(ticker['c']),
                                'volume': float(ticker['v']),
                                'timestamp': datetime.fromtimestamp(ticker['E']/1000),
                                'price_change': float(ticker['c']) - float(ticker['o']),
                                'price_change_percent': ((float(ticker['c']) - float(ticker['o'])) / float(ticker['o'])) * 100
                            }
                except Exception as e:
                    print(f"WebSocket error: {e}")
                    await asyncio.sleep(5)  # Wait before reconnecting
                    
    def get_all_tickers(self):
        return list(self.cached_data.values())

    def get_top_tickers(self, limit=20):
        # Sort by volume and return top N tickers
        sorted_tickers = sorted(
            self.cached_data.values(), 
            key=lambda x: float(x['volume']), 
            reverse=True
        )
        return sorted_tickers[:limit]

# Create a global instance
binance_stream = BinanceDataStream()

# Start WebSocket connection
def start_websocket():
    asyncio.run(binance_stream.connect_websocket())

# Run in a separate thread
import threading
websocket_thread = threading.Thread(target=start_websocket)
websocket_thread.daemon = True
websocket_thread.start()

# Update your existing endpoints
@app.route('/get_top_coins')
def get_top_coins():
    return jsonify(binance_stream.get_top_tickers()) 

# Define intervals
INTERVALS: Dict[str, str] = {
    '1m': '1 minute',
    '3m': '3 minutes',
    '5m': '5 minutes',
    '15m': '15 minutes',
    '30m': '30 minutes',
    '1h': '1 hour',
    '2h': '2 hours',
    '4h': '4 hours',
    '6h': '6 hours',
    '8h': '8 hours',
    '12h': '12 hours',
    '1d': '1 day',
    '3d': '3 days',
    '1w': '1 week',
    '1M': '1 month'
}

# Add the new endpoint
@app.get("/get_intervals")
async def get_intervals():
    return INTERVALS

@app.route('/get_historical_data')
def get_historical_data():
    symbol = request.args.get('symbol', 'BTCUSDT')
    interval = request.args.get('interval', '1h')
    start_date = request.args.get('start_date')
    
    try:
        # Convert start_date string to timestamp
        start_ts = int(datetime.strptime(start_date, '%Y-%m-%d').timestamp() * 1000)
        
        # Get data from Binance
        klines = client.get_historical_klines(
            symbol,
            interval,
            start_str=start_ts,
            limit=1000  # Adjust limit as needed
        )
        
        # Format the data
        formatted_data = []
        for k in klines:
            formatted_data.append({
                'timestamp': k[0],
                'open': float(k[1]),
                'high': float(k[2]),
                'low': float(k[3]),
                'close': float(k[4]),
                'volume': float(k[5]),
                'close_time': k[6],
                'quote_volume': float(k[7])
            })
            
        return jsonify(formatted_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 400 