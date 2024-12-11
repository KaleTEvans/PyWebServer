################################################
# Process high frequency data on its own thread
################################################

import threading
import time
import queue
import pandas as pd

from app.cppserver_comms.models import (OptionDataModel, FiveSecDataModel, TimeAndSalesDataModel,
                                        UnderlyingOneMinDataModel, UnderlyingAveragesModel,
                                        TickDataModel, OneMinDataModel,
                                        UnderlyingContractModel, NewsEventModel)

class HFDataHandler:
    def __init__(self):
        self._incoming_data_queue = queue.Queue()

        # Sorted data containers
        self.news_data = pd.DataFrame(columns=["time", "date_time", "article_id", "headline", "sentiment_score"])
        self.underlying_extra_data = pd.DataFrame(columns=["call_open_interest", "put_open_interest"])
        self.underlying_candles = pd.DataFrame(
            columns=["time", "date_time", "open", "high", "low", "close", "daily_high", "daily_low", "total_call_volume", 
                     "total_put_volume", "index_future_premium", "option_implied_volatility"]
        )

        # Threading
        self._thread = None
        self._running = threading.Event()
        self._lock = threading.Lock()

    def start(self):
        print("Starting HF data handler thread.")
        if self._thread is None:
            self._running.set()
            self._thread = threading.Thread(target=self._process_data_queue)
            self._thread.start()

    def stop(self):
        print("Stopping HF data handler thread.")
        if self._thread is not None:
            self._running.clear()
            self._thread.join()
            self._thread = None

    def add_new_data(self, pydantic_model):
        self._incoming_data_queue.put(pydantic_model)
            
    def _process_data_queue(self):
        while self._running.is_set():
            with self._lock:
                data = self._incoming_data_queue.get(timeout=1)
                if isinstance(data, NewsEventModel):
                    self._handle_news_data(data=data)

    def _handle_news_data(self, data: NewsEventModel):
        news_row = {
            "time": data.time,
            "date_time": data.date_time,
            "article_id": data.article_id,
            "headline": data.headline,
            "sentiment_score": data.sentiment_score
        }

        with self._lock:
            self.news_data = pd.concat([self.news_data, pd.DataFrame([news_row])]).reset_index(drop=True)

    def _handle_underlying_data(self, data: UnderlyingContractModel):
