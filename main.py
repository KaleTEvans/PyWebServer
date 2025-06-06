import asyncio

from app.websocket_client import WEBSOCKET_URL
from app.websocket_client import WebSocketClient
from typing import Union
from fastapi import FastAPI
from fastapi.testclient import TestClient
from fastapi.websockets import WebSocket
from contextlib import asynccontextmanager

from app.market_data_handling import hf_data_processor
from app.cppserver_comms import outbound
from app import websocket_server
from app.db_managment.db_inserter import DbInserter

from tests import cpp_ws_test
import threading

# Connect to cpp websocket instance
ws_client = WebSocketClient()
hf_data = hf_data_processor.HFDataHandler()

db_inserter = DbInserter()

@asynccontextmanager
async def lifespan(app: FastAPI):
    connect_task = asyncio.create_task(ws_client.connect())
    data_processing_task = asyncio.create_task(hf_data.start())
    # cpp_ws_test.start_cpp_ws_test()
    await outbound.add_ticker_to_scanner(symbol="SPX")
    await outbound.start_scanner()
    db_inserter.start()
    yield  
    db_inserter.stop()
    # Ensure the WebSocket is properly disconnected
    # cpp_ws_test.stop_cpp_ws_test()
    await ws_client.cleanup()
    data_processing_task.cancel()
    connect_task.cancel()

app = FastAPI(lifespan=lifespan)

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace with your React app URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"Hello": "World"}

app.include_router(outbound.outbound_cpp_ws_router)
app.include_router(hf_data_processor.option_data_router)
app.include_router(websocket_server.outbound_ws_react_router)

if __name__ == "__main__":
    try:
        import uvicorn
        uvicorn.run("main:app", host="0.0.0.0", port=8000, proxy_headers=True)
    except KeyboardInterrupt:
        print("Program interrupted by user. Exiting...")