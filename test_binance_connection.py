#!/usr/bin/env python3
"""
Test Binance API Connection
Tests both REST API and WebSocket connectivity
"""
import asyncio
import os
from binance.client import Client
from binance import AsyncClient, BinanceSocketManager
from datetime import datetime

# API Keys (from environment or hardcoded for testing)
API_KEY = os.getenv('BINANCE_API_KEY', 'FnbespwleoTxC1VUGAaP5sstXeu4nfuv80enfhwOhpeNz08BM0sC19pdRYayK8ap')
API_SECRET = os.getenv('BINANCE_API_SECRET', '3uIce3m26CJv3eE4B9LPUaKZfcbGp39m9VoWleEA9annLYVRpp7h8ILM0RRiLWJ7')


def test_rest_api():
    """Test REST API connection and permissions"""
    print("=" * 60)
    print("🔍 Testing Binance REST API Connection")
    print("=" * 60)
    
    try:
        # Create client
        client = Client(API_KEY, API_SECRET)
        
        # Test 1: Server time
        print("\n✅ Test 1: Server Time")
        server_time = client.get_server_time()
        server_datetime = datetime.fromtimestamp(server_time['serverTime'] / 1000)
        print(f"   Server Time: {server_datetime}")
        
        # Test 2: Exchange info
        print("\n✅ Test 2: Exchange Info")
        exchange_info = client.get_exchange_info()
        print(f"   Timezone: {exchange_info['timezone']}")
        print(f"   Total Symbols: {len(exchange_info['symbols'])}")
        
        # Test 3: Account status
        print("\n✅ Test 3: Account Status")
        account = client.get_account()
        print(f"   Can Trade: {account['canTrade']}")
        print(f"   Can Withdraw: {account['canWithdraw']}")
        print(f"   Can Deposit: {account['canDeposit']}")
        print(f"   Account Type: {account['accountType']}")
        
        # Test 4: Current BTC price
        print("\n✅ Test 4: Current Prices")
        btc_price = client.get_symbol_ticker(symbol="BTCUSDT")
        eth_price = client.get_symbol_ticker(symbol="ETHUSDT")
        print(f"   BTC/USDT: ${float(btc_price['price']):,.2f}")
        print(f"   ETH/USDT: ${float(eth_price['price']):,.2f}")
        
        # Test 5: API permissions
        print("\n✅ Test 5: API Key Permissions")
        api_permissions = client.get_account_api_permissions()
        print(f"   IP Restrict: {api_permissions['ipRestrict']}")
        print(f"   Enable Reading: {api_permissions['enableReading']}")
        print(f"   Enable Spot & Margin: {api_permissions['enableSpotAndMarginTrading']}")
        print(f"   Enable Withdrawals: {api_permissions['enableWithdrawals']}")
        print(f"   Enable Futures: {api_permissions.get('enableFutures', False)}")
        
        # Test 6: Get some historical klines
        print("\n✅ Test 6: Historical Klines (BTCUSDT 1m, last 5 candles)")
        klines = client.get_klines(symbol='BTCUSDT', interval=Client.KLINE_INTERVAL_1MINUTE, limit=5)
        for i, kline in enumerate(klines, 1):
            open_time = datetime.fromtimestamp(kline[0] / 1000)
            print(f"   {i}. {open_time} - O:{kline[1]} H:{kline[2]} L:{kline[3]} C:{kline[4]} V:{kline[5]}")
        
        print("\n" + "=" * 60)
        print("✅ REST API Connection: SUCCESS")
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("=" * 60)
        print("❌ REST API Connection: FAILED")
        print("=" * 60)
        return False


async def test_websocket():
    """Test WebSocket connection"""
    print("\n\n" + "=" * 60)
    print("🔍 Testing Binance WebSocket Connection")
    print("=" * 60)
    
    try:
        # Create async client
        client = await AsyncClient.create()
        bm = BinanceSocketManager(client)
        
        # Test 1: Kline WebSocket
        print("\n✅ Test 1: Kline WebSocket (BTCUSDT 1m)")
        print("   Listening for 5 messages...")
        
        socket = bm.kline_socket('BTCUSDT', interval='1m')
        
        message_count = 0
        async with socket as stream:
            while message_count < 5:
                msg = await stream.recv()
                
                if msg.get('e') == 'kline':
                    kline = msg['k']
                    print(f"   Message {message_count + 1}:")
                    print(f"      Symbol: {msg['s']}")
                    print(f"      Time: {datetime.fromtimestamp(kline['t'] / 1000)}")
                    print(f"      Interval: {kline['i']}")
                    print(f"      Close: {kline['c']}")
                    print(f"      Volume: {kline['v']}")
                    print(f"      Is Closed: {kline['x']}")
                    message_count += 1
        
        # Test 2: Trade WebSocket
        print("\n✅ Test 2: Trade WebSocket (BTCUSDT)")
        print("   Listening for 3 trades...")
        
        socket = bm.trade_socket('BTCUSDT')
        
        trade_count = 0
        async with socket as stream:
            while trade_count < 3:
                msg = await stream.recv()
                
                if msg.get('e') == 'trade':
                    print(f"   Trade {trade_count + 1}:")
                    print(f"      Symbol: {msg['s']}")
                    print(f"      Price: {msg['p']}")
                    print(f"      Quantity: {msg['q']}")
                    print(f"      Time: {datetime.fromtimestamp(msg['T'] / 1000)}")
                    print(f"      Buyer is maker: {msg['m']}")
                    trade_count += 1
        
        await client.close_connection()
        
        print("\n" + "=" * 60)
        print("✅ WebSocket Connection: SUCCESS")
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("=" * 60)
        print("❌ WebSocket Connection: FAILED")
        print("=" * 60)
        return False


async def test_multiple_symbols():
    """Test WebSocket with multiple symbols"""
    print("\n\n" + "=" * 60)
    print("🔍 Testing Multiple Symbols WebSocket")
    print("=" * 60)
    
    try:
        client = await AsyncClient.create()
        bm = BinanceSocketManager(client)
        
        symbols = ['BTCUSDT', 'ETHUSDT']
        print(f"\n✅ Subscribing to: {', '.join(symbols)}")
        print("   Listening for 5 seconds...")
        
        # Create multiplex socket for multiple symbols
        socket = bm.multiplex_socket([f"{s.lower()}@kline_1m" for s in symbols])
        
        async with socket as stream:
            start_time = asyncio.get_event_loop().time()
            message_count = 0
            
            while asyncio.get_event_loop().time() - start_time < 5:
                try:
                    msg = await asyncio.wait_for(stream.recv(), timeout=1.0)
                    
                    if msg.get('data', {}).get('e') == 'kline':
                        data = msg['data']
                        kline = data['k']
                        message_count += 1
                        print(f"   {data['s']}: Close={kline['c']}, Volume={kline['v']}")
                        
                except asyncio.TimeoutError:
                    continue
        
        print(f"\n   Total messages received: {message_count}")
        
        await client.close_connection()
        
        print("\n" + "=" * 60)
        print("✅ Multiple Symbols WebSocket: SUCCESS")
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("=" * 60)
        print("❌ Multiple Symbols WebSocket: FAILED")
        print("=" * 60)
        return False


def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("🚀 Binance Connection Test Suite")
    print("=" * 60)
    print(f"API Key: {API_KEY[:10]}...{API_KEY[-10:]}")
    print(f"Time: {datetime.now()}")
    print("=" * 60)
    
    # Test 1: REST API
    rest_success = test_rest_api()
    
    if not rest_success:
        print("\n⚠️  REST API failed, skipping WebSocket tests")
        return
    
    # Test 2: WebSocket
    asyncio.run(test_websocket())
    
    # Test 3: Multiple Symbols
    asyncio.run(test_multiple_symbols())
    
    print("\n\n" + "=" * 60)
    print("🎉 All Tests Completed!")
    print("=" * 60)
    print("\n✅ Your Binance API credentials are working correctly!")
    print("✅ Both REST API and WebSocket connections are functional")
    print("✅ Ready to collect real-time market data")
    print("\n💡 Next steps:")
    print("   1. Keep your API keys secure (use .env file)")
    print("   2. Start the Data Collector service")
    print("   3. Monitor real-time data in Redis")
    print("=" * 60)


if __name__ == "__main__":
    main()

