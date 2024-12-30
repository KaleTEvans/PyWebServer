###############################################################
# All underlying data is sent here
#
# Ticks and candles will be sent to outbound websocket
# Previous candles and extra data will be available via request
################################################################

from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
import asyncio

from utils.standard_dev import StreamingStatistics
from app.cppserver_comms.models import (UnderlyingContractModel, UnderlyingCandle, UnderlyingTick,
                                        UnderlyingExtraData, UnderlyingGeneral, OutboundWSData)

from app import websocket_server

###############################################
# All data handled here
###############################################

class UnderlyingDataHandler:
    def __init__(self, symbol):
        self.symbol = symbol

        self.call_open_interest: int = 0
        self.put_open_interest: int = 0
        self.futures_open_interest: int = 0
        self.low_13_week: float = 0
        self.high_13_week: float = 0
        self.low_26_week: float = 0
        self.high_26_week: float = 0
        self.low_52_week: float = 0
        self.high_52_weeK: float = 0
        self.daily_high: float = 0
        self.daily_low: float = 0
        self.last_option_iv: float = 0
        self.last_total_call_volume: float = 0
        self.last_total_put_volume: float = 0

        self.one_min_price_stats = StreamingStatistics()
        self.total_call_stats = StreamingStatistics()
        self.total_put_stats = StreamingStatistics()

        self.total_call_stats.add(0)
        self.total_call_stats.add(0)

        self.one_min_candles: List[UnderlyingCandle] = []

    def add_data(self, data: UnderlyingContractModel):
        if len(data.underlying_averages) > 0:
            for row in data.underlying_averages:
                if row.low_13_week != self.low_13_week: self.low_13_week = row.low_13_week
                if row.high_13_week != self.high_13_week: self.high_13_week = row.high_13_week
                if row.low_26_week != self.low_26_week: self.low_26_week = row.high_26_week
                if row.high_26_week != self.high_26_week: self.high_26_week = row.high_26_week
                if row.low_52_week != self.low_52_week: self.low_52_week = row.low_52_week
                if row.high_52_weeK != self.high_52_weeK: self.high_52_weeK = row.high_52_weeK

        if len(data.underlying_one_min) > 0:
            for row in data.underlying_one_min:
                if row.call_open_interest > 0: self.call_open_interest = row.call_open_interest
                if row.put_open_interest > 0: self.put_open_interest = row.put_open_interest
                if row.futures_open_interest > 0: self.futures_open_interest = row.futures_open_interest
                if row.daily_high > 0: self.daily_high = row.daily_high
                if row.daily_low > 0: self.daily_low = row.daily_low
                if row.option_implied_volatility > 0: self.last_option_iv = row.option_implied_volatility

                candle = UnderlyingCandle(
                    time=row.time,
                    date_time=row.date_time,
                    open=row.open,
                    high=row.high,
                    low=row.low,
                    close=row.close,
                    total_call_volume=row.total_call_volume,
                    total_put_volume=row.total_put_volume,
                    option_implied_volatility=self.last_option_iv
                )

                print(candle)

                # Update statistic values
                candle_returns = ((row.close - row.open) / row.open) * 100
                self.one_min_price_stats.add(candle_returns)
                candle.candle_returns = candle_returns

                call_volume_delta = row.total_call_volume - self.last_total_call_volume
                self.total_call_stats.add(call_volume_delta)
                candle.call_volume_delta = call_volume_delta
                self.last_total_call_volume = row.total_call_volume

                put_volume_delta = row.total_put_volume - self.last_total_put_volume
                self.total_put_stats.add(put_volume_delta)
                candle.put_volume_delta = put_volume_delta
                self.last_total_put_volume = row.total_put_volume

                self.one_min_candles.append(candle)

                ##########################################
                # TODO: Add function to send to websocket
                ##########################################

                # await websocket_server.react_queue.put(candle.model_dump_json())

        if len(data.underlying_price_ticks) > 0:
            for row in data.underlying_price_ticks:
                tick = UnderlyingTick(
                    time=row.time,
                    price=row.price
                )

                underlying = UnderlyingGeneral(
                    symbol=self.symbol,
                    tick=tick
                )

                outbound = OutboundWSData(
                    type="underlying",
                    underlying=underlying
                )

                ##########################################
                # TODO: Add function to send to websocket
                ##########################################


                self.enqueue_ws_data(data=outbound.model_dump_json())

    def enqueue_ws_data(self, data):
        websocket_server.react_queue.put(data)

    def get_candles(self):
        return self.one_min_candles
    
    def get_extra_data(self):
        return UnderlyingExtraData(
            call_open_interest=self.call_open_interest,
            put_open_interest=self.put_open_interest,
            futures_open_interest=self.futures_open_interest,
            low_13_week=self.low_13_week,
            high_13_week=self.high_13_week,
            low_26_week=self.low_26_week,
            high_26_week=self.high_26_week,
            low_52_week=self.low_52_week,
            high_52_weeK=self.high_52_weeK,
            daily_high=self.daily_high,
            daily_low=self.daily_low,
            last_option_iv=self.last_option_iv
        )