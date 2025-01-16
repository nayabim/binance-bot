import asyncio
import websockets
import json
from datetime import datetime

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