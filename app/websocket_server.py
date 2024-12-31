########################################################
# Used for sending streaming data to the client web app
########################################################

from app.cppserver_comms.models import OutboundWSData
from typing import List

from fastapi import WebSocket, APIRouter, WebSocketDisconnect
from fastapi.encoders import jsonable_encoder
import asyncio
import threading
import queue

# Add all items to this that will be sent to the react webpage
react_queue = asyncio.Queue()

outbound_ws_react_router = APIRouter(prefix="/hf-data")

@outbound_ws_react_router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("Client Connected.")
    try:
        # batch: List[OutboundWSData] = []
        while True:
            # Grab data from the async queue
            data: OutboundWSData = await react_queue.get()
            # batch.append(jsonable_encoder(data))
            await websocket.send_json(jsonable_encoder(data))

    except WebSocketDisconnect:
        print("Client disconnected.")
