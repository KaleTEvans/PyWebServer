import ssl
import asyncio
import websockets
from websockets import ConnectionClosed
from utils.singleton import Singleton
from proto import messages_pb2  # Import generated Protobuf models
import os
from dotenv import load_dotenv
import threading
import queue

from app.cppserver_comms.inbound import WSDataHandler

# Load WebSocket URL from .env file
load_dotenv()
WEBSOCKET_URL = os.getenv("WEBSOCKET_URL")
CA_CERT_PATH = "/home/kale/dev/TWSStrategyCPPServer/IntradayStrategyBuilder/third_party_libs/CppServer/tools/certificates/ca.crt"

class WebSocketClient(metaclass=Singleton):
	def __init__(self):
		self.url = WEBSOCKET_URL
		self.is_connected = False
		self.websocket = None  # Hold the current WebSocket connection
		

		self.msg_send_queue = asyncio.Queue()
		self.data_handler = WSDataHandler()

	async def connect(self):
		"""Establish a connection to the WebSocket server."""
		ssl_context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
		ssl_context.load_verify_locations(CA_CERT_PATH)

		try:
			self.websocket = await websockets.connect(self.url, ssl=ssl_context)
			self.is_connected = True
			print(f"Connected to WebSocket server: {self.url}")

			# Start the data handler
			asyncio.create_task(self.data_handler.start())

			await asyncio.gather(self._listen(), self._process_outbound_messages())

		except Exception as e:
			print(f"Error during WebSocket connection: {e}")
		finally:
			await self.cleanup()

	async def _listen(self):
		"""Listen for incoming messages from the WebSocket server."""
		while self.is_connected:
			try:
				message = await self.websocket.recv()
				await self.data_handler.receive_ws_message(message=message)
			except Exception as e:
				print(f"Error receiving message: {e}")
				break

	async def _process_outbound_messages(self):
		"""Send messages from the outbound queue to the WebSocket server."""
		try:
			while self.is_connected:
				message = await self.msg_send_queue.get()
				await self.websocket.send(message)
				print(f"Sent message to server: {message}")
		except ConnectionClosed as e:
			print(f"Outbound message task stopped: {e}")
		except asyncio.CancelledError:
			print("Outbound queue task was cancelled.")
		except Exception as e:
			print(f"Error during message sending: {e}")

	async def send_message(self, message):
		"""Add a message to the outbound queue."""
		await self.msg_send_queue.put(message)
		print(f"Message queued for sending: {message}")

	# async def _send_ping(self):
	# 	"""Periodically send pings to the server to keep the connection alive."""
	# 	while self.is_connected:
	# 		try:
	# 			pong_waiter = await self.websocket.ping()
	# 			await pong_waiter  # Wait for the pong
	# 			print("Pong received")
	# 		except Exception as e:
	# 			print(f"Ping/Pong error: {e}")
	# 			self.is_connected = False
	# 			break
	# 		await asyncio.sleep(10)  # Ping interval

	async def cleanup(self):
		"""Clean up resources and close the WebSocket connection."""
		self.is_connected = False
		self.keep_running = False
		if self.websocket:
			await self.websocket.close()
			print("WebSocket connection closed.")
		print("Cleanup completed.")
