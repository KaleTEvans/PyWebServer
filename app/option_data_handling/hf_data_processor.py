################################################
# Process high frequency data on its own thread
################################################

import threading
import time
import queue
import asyncio

from app.cppserver_comms.models import (OptionDataModel, FiveSecDataModel, TimeAndSalesDataModel,
                                        UnderlyingOneMinDataModel, UnderlyingAveragesModel,
                                        UnderlyingPriceTickModel ,TickDataModel, OneMinDataModel,
                                        UnderlyingContractModel, NewsEventModel, UnderlyingCandle,
                                        UnderlyingExtraData, TimeAndSalesByMinute)

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from typing import List

from utils.singleton import Singleton
from app.option_data_handling.underlying_data_handler import UnderlyingDataHandler
from app.option_data_handling.option_data_handler import OptionDataHandler

option_data_router = APIRouter(prefix="/option-data")

# Get candles with just olhc data
# Get all single data points of interest, ie OI, daily high/low, etc
# Sort contracts into a dict
# Create filter for RT volume
# Tally up all incoming RT volume to get total flow, such as buys at bid, call volume, etc
# Build model to track averages and stdev to locate price/volume spikes

class HFDataHandler(metaclass=Singleton):
    def __init__(self):
        self._incoming_data_queue = asyncio.Queue()

        # Sorted data containers
        self.underlying_data: dict[str, UnderlyingDataHandler] = {}
        self.option_data: dict[str, OptionDataHandler] = {}
        self.news_objects: List[NewsEventModel] = []

    async def start(self):
        print("Starting HF data handler.")
        asyncio.create_task(self._process_data_queue())

    def stop(self):
        print("Stopping HF data handler.")

    async def add_new_data(self, pydantic_model):
        await self._incoming_data_queue.put(pydantic_model)
            
    async def _process_data_queue(self):
        while True:
            try:
                data = await self._incoming_data_queue.get()
                if isinstance(data, NewsEventModel):
                    self._handle_news_data(data=data)
                elif isinstance(data, UnderlyingContractModel):
                    await self._handle_underlying_data(data=data)
                elif isinstance(data, OptionDataModel):
                    self._handle_option_data(data=data)
                else:
                    print("Data not matched with any models.")
                    continue
            except self._incoming_data_queue.empty():
                continue
            except Exception as e:
                print(f"HF Data Queue error: {e}")

    def _handle_news_data(self, data: NewsEventModel):
        try:
            self.news_objects.append(data)
        except Exception as e:
            print(f"Error handling news data: {e}")

    def get_news_data(self):
        return self.news_objects

    async def _handle_underlying_data(self, data: UnderlyingContractModel):
        if data.symbol not in self.underlying_data.keys():
            underlying_data = UnderlyingDataHandler(data.symbol)
            self.underlying_data[data.symbol] = underlying_data
            print(f"New ticker added to UnderlyingData: {data.symbol}")

        await self.underlying_data[data.symbol].add_data(data=data)

    def _handle_option_data(self, data: OptionDataModel):
        if data.symbol not in self.option_data.keys():
            option_data = OptionDataHandler(data.symbol)
            self.option_data[data.symbol] = option_data

        self.option_data[data.symbol].add_data(data=data)
        

hf_data = HFDataHandler() 

# @option_data_router.get("/news", response_model=List[NewsEventModel])
# async def get_news_data():
#     return hf_data.get_news_data()

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

@option_data_router.get("/{ticker}/option/time-and-sales-by-minute", response_model=TimeAndSalesByMinute)
async def get_time_and_sales_by_minute(ticker):
    if ticker in hf_data.option_data.keys():
        return hf_data.option_data[ticker].get_tas_aggregate_data()
    else:
        print(f"No underlying data found for ticker: {ticker}")