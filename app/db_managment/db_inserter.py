import psycopg2
from pgcopy import CopyManager
from datetime import datetime, timedelta
from pytz import timezone
from dotenv import load_dotenv
import os
from utils.singleton import Singleton
import threading
import queue

import psycopg2.extras

load_dotenv()

db_params = {
    "host": os.getenv("HOST_URL"),
    "database": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASS"),
    "port": os.getenv("DB_PORT")
}

def get_db_connection():
    return psycopg2.connect(**db_params)

class DbInserter(metaclass=Singleton):
    def __init__(self):
        self.conn = get_db_connection()

        self.thread = None
        self.running = threading.Event()
        self.lock = threading.Lock()
        self.stop_event = threading.Event()

        self.db_queue = queue.Queue()

        self.underlying_sig_prices_cols = [
            'time', 
            'low_13_week', 
            'high_13_week', 
            'low_26_week', 
            'high_26_week', 
            'low_52_week', 
            'high_52_week',
            'call_open_interest',
            'put_open_interest',
            'futures_open_interest'
        ]
        self.underlying_sig_prices_data = []

        self.underlying_one_min_cols = [
            'time',
            'unix_time',
            'open',
            'high',
            'low',
            'close',
            'daily_high',
            'daily_low',
            'total_call_volume',
            'total_put_volume',
            'option_implied_volatility'
        ]
        self.underlying_one_min_data = []

        self.rt_trade_cols = [
            'time',
            'unix_time',
            'symbol',
            'option_right',
            'strike',
            'price',
            'quantity',
            'total_cost',
            'total_volume',
            'vwap',
            'current_ask',
            'current_bid',
            'current_rtm'
        ]
        self.rt_trade_data = []

    def start(self):
        print("Starting db insertion thread.")
        if self.thread is None:
            self.running.set()
            self.stop_event.clear()
            self.thread = threading.Thread(target=self.insert_data)
            self.thread.start()

    def stop(self):
        print("Stopping db insertion thread.")
        if self.thread is not None:
            self.running.clear()
            self.stop_event.set()
            self.thread.join()
            self.thread = None

    def create_underlying_sig_prices_row(
        self,
        timestammp: datetime,
        low_13_week: float,
        high_13_week: float,
        low_26_week: float,
        high_26_week: float,
        low_52_week: float,
        high_52_week: float,
        call_open_interest: int,
        put_open_interest: int,
        futures_open_interest: int
    ):
        self.underlying_sig_prices_data.append(
            (timestammp, low_13_week, high_13_week, low_26_week, high_26_week, low_52_week, high_52_week,
             int(call_open_interest), int(put_open_interest), int(futures_open_interest))
        )

    def create_underlying_one_min_row(
        self,
        date_time: datetime,
        time: int,
        open: float,
        high: float,
        low: float,
        close: float,
        daily_high: float,
        daily_low: float,
        total_call_volume: int,
        total_put_volume: int,
        option_implied_volatility: float
    ):
        self.underlying_one_min_data.append(
            (date_time, time, open, high, low, close, daily_high, daily_low, total_call_volume, 
             total_put_volume, option_implied_volatility)
        )

    def create_rt_trade_row(
        self,
        time: datetime,
        unix_time: int,
        symbol: str,
        right: str,
        strike: int,
        price: float,
        quantity: int,
        total_cost: float,
        total_volume: int,
        vwap: float,
        current_ask: float,
        current_bid: float,
        current_rtm: str
    ):
        self.rt_trade_data.append(
            (time, unix_time, symbol, right, strike, price, quantity, total_cost, total_volume, vwap,
             current_ask, current_bid, current_rtm)
        )
    
    def insert_data(self):

        underlying_sig_prices_mgr = CopyManager(self.conn, 'spx_underlying_significant_prices', self.underlying_sig_prices_cols)
        underlying_one_min_mgr = CopyManager(self.conn, 'spx_underlying_one_minute_data', self.underlying_one_min_cols)
        rt_trade_mgr = CopyManager(self.conn, 'rt_trades', self.rt_trade_cols)

        while self.running.is_set() and not self.stop_event.is_set():
            if len(self.underlying_sig_prices_data) >= 1:
                underlying_sig_prices_mgr.copy(self.underlying_sig_prices_data)
                self.conn.commit()
                print("Underlying Significant Prices Inserted Successfully")

                self.underlying_sig_prices_data.clear()

            if len(self.underlying_one_min_data) >= 5:
                underlying_one_min_mgr.copy(self.underlying_one_min_data)
                self.conn.commit()
                print("Underlying One Minute Data Inserted Successfully")

                self.underlying_one_min_data.clear()

            if len(self.rt_trade_data) >= 50:
                rt_trade_mgr.copy(self.rt_trade_data)
                self.conn.commit()
                print("Rt Trade data inserted successfully.")

                self.rt_trade_data.clear()



