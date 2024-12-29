from app.cppserver_comms.models import UnderlyingContractModel, NewsEventModel
from app.cppserver_comms.inbound import WSDataHandler

import threading
import time

test_thread = None
stop_event = threading.Event()

def generate_random_objects():
    time_passed = 0
    prev_price = 5950
    data_handler = WSDataHandler()

    while not stop_event.is_set():
        underlying_tick = UnderlyingContractModel.random_tick(prev=prev_price)
        prev_price = underlying_tick.underlying_price_ticks[0].price
        data_handler.handle_formatted_messages(pydantic_model=underlying_tick)

        if time_passed % 30 == 0:
            news = NewsEventModel.random()
            data_handler.handle_formatted_messages(pydantic_model=news)

        time.sleep(0.250)
        time_passed += 0.250

def start_cpp_ws_test():
    global test_thread
    if test_thread is None:
        test_thread = threading.Thread(target=generate_random_objects, daemon=True)
        test_thread.start()

def stop_cpp_ws_test():
    global test_thread
    if test_thread is not None:
        stop_event.set()
        test_thread.join()
        test_thread = None

