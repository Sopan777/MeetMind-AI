import asyncio
import websockets
import json

async def test():
    uri = "ws://127.0.0.1:8000/ws/analyze"
    print(f"Connecting to {uri}...")
    try:
        async with websockets.connect(uri) as ws:
            print("Connected!")
            # Send start message
            await ws.send(json.dumps({"type": "start", "meeting_id": "test-123"}))
            response = await asyncio.wait_for(ws.recv(), timeout=5)
            print("Server response:", response)
            await ws.send(json.dumps({"type": "stop"}))
            print("WebSocket test PASSED!")
    except Exception as e:
        print(f"WebSocket test FAILED: {type(e).__name__}: {e}")

asyncio.run(test())
