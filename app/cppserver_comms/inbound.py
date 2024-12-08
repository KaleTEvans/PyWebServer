import asyncio
from proto import messages_pb2 
from utils.singleton import Singleton

# Handle all incoming messages from the CPP Server here
class WSDataHandler(metaclass=Singleton):
    def __init__(self):
        self.message_queue = asyncio.Queue()

    async def start(self):
        asyncio.create_task(self.process_ws_messages())

    async def receive_ws_message(self, message):
        await self.message_queue.put(message)

    async def process_ws_messages(self):
        while True:
            try:
                message = await self.message_queue.get()
                parsed_message = messages_pb2.Message()
                parsed_message.ParseFromString(message)
                print(f"Received message: {parsed_message}")
            except Exception as e:
                print(f"Failed to parse incoming message: {e}")
                continue
