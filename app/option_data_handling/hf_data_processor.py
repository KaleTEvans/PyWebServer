################################################
# Process high frequency data on its own thread
################################################

import threading
import time
import queue
import pandas as pd

from app.cppserver_comms.models import (OptionDataModel, FiveSecDataModel, TimeAndSalesDataModel,
                                        UnderlyingOneMinDataModel, UnderlyingAveragesModel,
                                        UnderlyingPriceTickModel ,TickDataModel, OneMinDataModel,
                                        UnderlyingContractModel, NewsEventModel)

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from typing import List

from utils.singleton import Singleton
from app.option_data_handling.underlying_data_handler import UnderlyingDataHandler, UnderlyingCandle, UnderlyingExtraData

option_data_router = APIRouter(prefix="/option-data")

# Get candles with just olhc data
# Get all single data points of interest, ie OI, daily high/low, etc
# Sort contracts into a dict
# Create filter for RT volume
# Tally up all incoming RT volume to get total flow, such as buys at bid, call volume, etc
# Build model to track averages and stdev to locate price/volume spikes

class HFDataHandler(metaclass=Singleton):
    def __init__(self):
        self._incoming_data_queue = queue.Queue()

        # Sorted data containers
        self.news_data = pd.DataFrame(columns=["time", "date_time", "article_id", "headline", "sentiment_score"])
        self.underlying_data: dict[str, UnderlyingDataHandler] = {}

        self.news_objects: List[NewsEventModel] = []

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
            try:
                data = self._incoming_data_queue.get(timeout=1)
                if isinstance(data, NewsEventModel):
                    self._handle_news_data(data=data)
                elif isinstance(data, UnderlyingContractModel):
                    self._handle_underlying_data(data=data)
                elif isinstance(data, OptionDataModel):
                    self._handle_option_data(data=data)
                else:
                    print("Data not matched with any models.")
                    continue
            except queue.Empty:
                continue
            except Exception as e:
                print(f"HF Data Queue error: {e}")

    def _handle_news_data(self, data: NewsEventModel):
        try:
            with self._lock:
                self.news_objects.append(data)
                self.news_data = pd.concat([self.news_data, pd.DataFrame([data.__dict__])]).reset_index(drop=True)
        except Exception as e:
            print(f"Error handling news data: {e}")

    def get_news_data(self):
        with self._lock:
            return self.news_objects

    def _handle_underlying_data(self, data: UnderlyingContractModel):
        if data.symbol not in self.underlying_data.keys():
            underlying_data = UnderlyingDataHandler(data.symbol)
            self.underlying_data[data.symbol] = underlying_data
            print(f"New ticker added to UnderlyingData: {data.symbol}")

        self.underlying_data[data.symbol].add_data(data=data)

    def _handle_option_data(self, data: OptionDataModel):
        return
        

hf_data = HFDataHandler() 

@option_data_router.get("/news", response_model=List[NewsEventModel])
async def get_news_data():
    return hf_data.get_news_data()

@option_data_router.get("/{ticker}/underlying/get-today-candles", response_model=List[UnderlyingCandle])
async def get_underlying_candles(ticker):
    if ticker in hf_data.underlying_data.keys():
        return hf_data.underlying_data[ticker].get_candles()
    else:
        print(f"No underlying data found for ticker: {ticker}")

@option_data_router.get("/{ticker}/underlying/extra-data", response_model=UnderlyingExtraData)
async def get_underlying_extra_data(ticker):
    if ticker in hf_data.underlying_data.keys():
        return hf_data.underlying_data[ticker].get_extra_data()
    else:
        print(f"No underlying data found for ticker: {ticker}")