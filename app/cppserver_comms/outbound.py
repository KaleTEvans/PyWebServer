from fastapi import APIRouter
from proto import messages_pb2
from app.cppserver_comms.models import MessageModel
from app.websocket_client import WebSocketClient

ws_client = WebSocketClient()

outbound_cpp_ws_router = APIRouter(prefix="/send-msg")

@outbound_cpp_ws_router.post("/")
async def send_message(message: MessageModel):
    # Convert to protobuf message
    proto_msg = messages_pb2.Message()
    proto_msg.type = message.type

    if message.basic_message:
        basic_message = messages_pb2.BasicMessage()
        basic_message.message = message.basic_message.message
        proto_msg.basic_message.CopyFrom(basic_message)
    
    if message.confirmation:
        confirmation = messages_pb2.Confirmation()
        confirmation.action = message.confirmation.action
        confirmation.status = message.confirmation.status
        proto_msg.confirmation.CopyFrom(confirmation)

    # Serialize the Protobuf message
    serialized_message = proto_msg.SerializeToString()
    await ws_client.send_message(serialized_message)
    #return {"status": "Message sent", "serialized": serialized_message}

cpp_scanner_router = APIRouter(prefix="/scanner")

@cpp_scanner_router.post("/start")
async def start_scanner():
    isb_action = messages_pb2.ISBAction()
    isb_action.action = "start"
    isb_action.component = "option_scanner"

    proto_msg = messages_pb2.Message()
    proto_msg.type = "isb_action"
    proto_msg.isb_action.CopyFrom(isb_action)

    serialized_msg = proto_msg.SerializeToString()
    await ws_client.send_message(serialized_msg)

@cpp_scanner_router.post("/stop")
async def start_scanner():
    isb_action = messages_pb2.ISBAction()
    isb_action.action = "stop"
    isb_action.component = "option_scanner"

    proto_msg = messages_pb2.Message()
    proto_msg.type = "isb_action"
    proto_msg.isb_action.CopyFrom(isb_action)

    serialized_msg = proto_msg.SerializeToString()
    await ws_client.send_message(serialized_msg)

@cpp_scanner_router.post("/add-ticker")
async def add_ticker_to_scanner(symbol: str):
    isb_action = messages_pb2.ISBAction()
    isb_action.action = "add_ticker"
    isb_action.component = "option_scanner"
    isb_action.data = symbol

    proto_msg = messages_pb2.Message()
    proto_msg.type = "isb_action"
    proto_msg.isb_action.CopyFrom(isb_action)

    serialized_msg = proto_msg.SerializeToString()
    await ws_client.send_message(serialized_msg)


outbound_cpp_ws_router.include_router(cpp_scanner_router)