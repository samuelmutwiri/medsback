# test_websocket_complete.py
import asyncio
import websockets
import json
import sys

async def test_websocket():
    uri = "ws://localhost:8000/ws/notifications/"
    
    print(f"Testing WebSocket connection to: {uri}")
    print("-" * 50)
    
    try:
        # Connect
        async with websockets.connect(uri) as websocket:
            print("✅ Connected to WebSocket server")
            
            # Receive welcome message
            try:
                welcome = await asyncio.wait_for(websocket.recv(), timeout=5)
                print(f"✅ Received welcome: {welcome}")
                
                # Parse to verify it's valid JSON
                welcome_data = json.loads(welcome)
                print(f"✅ Welcome parsed: {welcome_data}")
                
            except asyncio.TimeoutError:
                print("❌ Timeout waiting for welcome message")
                return
            except json.JSONDecodeError:
                print("❌ Welcome message is not valid JSON")
                return
            
            # Test 1: Send JSON message
            print("\n" + "="*50)
            print("Test 1: Sending JSON message")
            print("="*50)
            
            test_message = {
                "action": "test",
                "data": "Hello WebSocket!",
                "timestamp": "2025-12-21"
            }
            
            print(f"Sending: {json.dumps(test_message)}")
            await websocket.send(json.dumps(test_message))
            print("✅ Message sent")
            
            # Receive response
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=5)
                print(f"✅ Response received: {response}")
                
                # Parse response
                response_data = json.loads(response)
                print(f"✅ Response parsed: {response_data}")
                
            except asyncio.TimeoutError:
                print("❌ Timeout waiting for response")
                return
            
            # Test 2: Send plain text (not JSON)
            print("\n" + "="*50)
            print("Test 2: Sending plain text")
            print("="*50)
            
            plain_text = "This is plain text, not JSON"
            print(f"Sending: {plain_text}")
            await websocket.send(plain_text)
            print("✅ Plain text sent")
            
            # Receive response
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=5)
                print(f"✅ Response received: {response}")
                
                # Try to parse (should work since server sends JSON)
                response_data = json.loads(response)
                print(f"✅ Response parsed: {response_data}")
                
            except asyncio.TimeoutError:
                print("❌ Timeout waiting for response")
                return
            
            # Test 3: Send multiple messages
            print("\n" + "="*50)
            print("Test 3: Sending multiple messages")
            print("="*50)
            
            for i in range(3):
                msg = {"message": f"Test message {i+1}", "count": i+1}
                print(f"Sending {i+1}: {msg}")
                await websocket.send(json.dumps(msg))
                
                response = await asyncio.wait_for(websocket.recv(), timeout=5)
                print(f"Response {i+1}: {response}")
                await asyncio.sleep(0.5)  # Small delay
            
            print("\n" + "="*50)
            print("✅ All tests completed successfully!")
            print("="*50)
            
            # Keep connection open a bit longer
            await asyncio.sleep(1)
            
    except ConnectionRefusedError:
        print("❌ Connection refused. Is the server running?")
        print("Run: python manage.py runserver")
    except websockets.exceptions.InvalidStatusCode as e:
        print(f"❌ Invalid status code: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_websocket())