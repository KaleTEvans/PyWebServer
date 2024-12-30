########################################################
# Used for sending streaming data to the client web app
########################################################

from fastapi import WebSocket, APIRouter, WebSocketDisconnect
import asyncio
import threading
import queue
import json

ws_server_thread = None
stop_event = threading.Event()

# Add all items to this that will be sent to the react webpage
react_queue = queue.Queue()

outbound_ws_react_router = APIRouter(prefix="/hf-data")

@outbound_ws_react_router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("Client Connected.")
    try:
        batch = []
        while True:
            while not react_queue.empty():
                # Grab data from the async queue
                batch.append(react_queue.get())
            
            if batch:
                await websocket.send_json(batch)
                batch = []

            # Send batch every 100ms
            await asyncio.sleep(0.1)

    except WebSocketDisconnect:
        print("Client disconnected.")
