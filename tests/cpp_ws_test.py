from app.cppserver_comms.models import UnderlyingContractModel, NewsEventModel
from app.cppserver_comms.inbound import WSDataHandler

import threading
import time
import asyncio
from datetime import datetime

test_thread = None
stop_event = threading.Event()

async def wait_for_even_minute():
    """
    Wait until the current time aligns with an even minute.
    """
    while True:
        now = datetime.now()
        if now.second == 0 and now.minute % 2 == 0:
            break
        await asyncio.sleep(0.5)  # Check every 0.5 seconds

async def generate_random_objects():
    print("Waiting for even minute to begin generating data")
    await wait_for_even_minute()
    
    time_passed = 0
    prev_price = 5950
    one_min_prices = []
    max_price = 0
    min_price = 10000
    data_handler = WSDataHandler()

    while not stop_event.is_set():
        one_min_prices.append(prev_price)
        max_price = max(max_price, prev_price)
        min_price = min(min_price, prev_price)
        underlying_tick = UnderlyingContractModel.random_tick(prev=prev_price)
        prev_price = underlying_tick.underlying_price_ticks[0].price
        await data_handler.handle_formatted_messages(pydantic_model=underlying_tick)

        if time_passed % 60 == 0:
            open = one_min_prices[0]
            high = max(one_min_prices)
            low = min(one_min_prices)
            close = one_min_prices[-1]
            dh = max_price
            dl = min_price
            one_min = UnderlyingContractModel.random_candles(open=open,high=high,low=low,close=close,max_price=dh,min_price=dl)
            await data_handler.handle_formatted_messages(pydantic_model=one_min)
            one_min_prices.clear()

            # Set prev_price to the close price to match candle open with close
            prev_price = close

        time.sleep(0.250)
        time_passed += 0.250

def start_cpp_ws_test():
    global test_thread
    if test_thread is None:
        # Start the async function in a thread
        def run_event_loop():
            asyncio.run(generate_random_objects())
        
        test_thread = threading.Thread(target=run_event_loop, daemon=True)
        test_thread.start()

def stop_cpp_ws_test():
    global test_thread
    if test_thread is not None:
        stop_event.set()
        test_thread.join()
        test_thread = None

