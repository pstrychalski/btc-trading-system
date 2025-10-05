#!/usr/bin/env python3
"""
Simple test of Data Collector without Redis
Just WebSocket streaming to console
"""
import asyncio
from datetime import datetime
from binance import AsyncClient, BinanceSocketManager

API_KEY = 'FnbespwleoTxC1VUGAaP5sstXeu4nfuv80enfhwOhpeNz08BM0sC19pdRYayK8ap'
API_SECRET = '3uIce3m26CJv3eE4B9LPUaKZfcbGp39m9VoWleEA9annLYVRpp7h8ILM0RRiLWJ7'


async def stream_market_data():
    """Stream real-time market data from Binance"""
    print("=" * 80)
    print("📡 Starting Real-Time Data Collector")
    print("=" * 80)
    print(f"Symbols: BTCUSDT, ETHUSDT")
    print(f"Intervals: 1m")
    print(f"Time: {datetime.now()}")
    print("=" * 80)
    print("\n🔄 Connecting to Binance WebSocket...")
    
    client = await AsyncClient.create(API_KEY, API_SECRET)
    bm = BinanceSocketManager(client)
    
    # Subscribe to BTC and ETH klines
    symbols = ['BTCUSDT', 'ETHUSDT']
    
    print(f"✅ Connected! Streaming data for {', '.join(symbols)}...")
    print("=" * 80)
    print("\n📊 Real-Time Market Data:\n")
    
    message_count = 0
    closed_candles = 0
    
    try:
        # Create multiplex socket for both symbols
        streams = [f"{s.lower()}@kline_1m" for s in symbols]
        socket = bm.multiplex_socket(streams)
        
        async with socket as stream:
            while message_count < 20:  # Run for 20 messages
                msg = await stream.recv()
                
                if msg.get('data', {}).get('e') == 'kline':
                    data = msg['data']
                    kline = data['k']
                    
                    message_count += 1
                    
                    # Format time
                    timestamp = datetime.fromtimestamp(kline['t'] / 1000)
                    
                    # Color codes
                    is_closed = kline['x']
                    close_marker = "🔒 CLOSED" if is_closed else "⏱️  OPEN"
                    
                    if is_closed:
                        closed_candles += 1
                    
                    # Print formatted message
                    print(f"{close_marker} | {data['s']:8} | {timestamp.strftime('%H:%M:%S')} |", end=" ")
                    print(f"O:{float(kline['o']):>10,.2f} |", end=" ")
                    print(f"H:{float(kline['h']):>10,.2f} |", end=" ")
                    print(f"L:{float(kline['l']):>10,.2f} |", end=" ")
                    print(f"C:{float(kline['c']):>10,.2f} |", end=" ")
                    print(f"V:{float(kline['v']):>8,.4f}")
                    
                    # Print summary every 5 messages
                    if message_count % 5 == 0:
                        print(f"\n{'─' * 80}")
                        print(f"   📈 Messages: {message_count} | Closed Candles: {closed_candles}")
                        print(f"{'─' * 80}\n")
        
        await client.close_connection()
        
        print("\n" + "=" * 80)
        print(f"✅ Data Collection Complete!")
        print(f"   Total Messages: {message_count}")
        print(f"   Closed Candles: {closed_candles}")
        print(f"   Open Candles: {message_count - closed_candles}")
        print("=" * 80)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        await client.close_connection()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        await client.close_connection()


if __name__ == "__main__":
    print("\n🚀 BTC Trading System - Data Collector Test\n")
    asyncio.run(stream_market_data())
    print("\n✨ Test completed!\n")

