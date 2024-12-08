import asyncio

from app.websocket_client import WEBSOCKET_URL
from app.websocket_client import WebSocketClient
from typing import Union
from fastapi import FastAPI
from contextlib import asynccontextmanager

# Connect to cpp websocket instance
ws_client = WebSocketClient()

@asynccontextmanager
async def lifespan(app: FastAPI):
    connect_task = asyncio.create_task(ws_client.connect())
    yield  
    # Ensure the WebSocket is properly disconnected
    await ws_client.cleanup()
    connect_task.cancel()

app = FastAPI(lifespan=lifespan)

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/items/{item_id}")
def read_item(item_id: int, q: Union[str, None] = None):
    return {"item_id": item_id, "q": q}

from app.cppserver_comms import outbound, inbound

app.include_router(outbound.outbound_cpp_ws_router)

if __name__ == "__main__":
    try:
        import uvicorn
        uvicorn.run("isb:app", host="0.0.0.0", port=8000, proxy_headers=True)
    except KeyboardInterrupt:
        print("Program interrupted by user. Exiting...")