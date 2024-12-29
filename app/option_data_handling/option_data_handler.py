###############################################################
# All option data is sent here and stored in associated option object
#
# Ticks and candles will be sent to outbound websocket
# Previous candles and extra data will be available via request
################################################################

# Items Needed:
# Time series for trades at bid/ask/mid
# Function for total vol at bid/ask/mid


from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

from utils.standard_dev import StreamingStatistics
from app.cppserver_comms.models import OptionDataModel, FiveSecDataModel, OneMinDataModel

class SingleOptionData:
    def __init__(self, symbol, right, current_rtm=None, strike=None):
        self.symbol: str = symbol
        self.right: str = right
        self.current_rtm: str = current_rtm
        self.strike: int = strike

        self.total_trade_count: int = 0 
        self.total_volume: int = 0 

        self.current_ask: float = 0
        self.current_bid: float = 0
        self.daily_volume_at_ask: int = 0
        self.daily_volume_at_bid: int = 0
        self.daily_volume_between: int = 0

        self.five_sec_candles: List[FiveSecDataModel] = []
        self.one_min_candles: List[OneMinDataModel] = []

    def add_five_sec_data(self, data: FiveSecDataModel): self.five_sec_candles.append(data)
    def add_one_min_data(self, data: OneMinDataModel): self.one_min_candles.append(data)


class OptionDataHandler:
    def __init__(self, symbol):
        self.symbol = symbol
        self.exp_date: str = ""

        self.current_chain: set[int] = set()
        self.tracked_calls: dict[int, SingleOptionData] = {}
        self.tracked_puts: dict[int, SingleOptionData] = {}
        self.calls_by_rtm: dict[str, SingleOptionData] = {}
        self.puts_by_rtm: dict[str, SingleOptionData] = {}

        self.total_volume_at_ask: int = 0
        self.total_colume_at_bid: int = 0
        self.total_volume_between: int = 0

    def update_exp_date(self, exp_date): self.exp_date = exp_date

    def add_data(self, data: OptionDataModel):
        if self.exp_date == "" : self.exp_date = data.exp_date
        if data.strike not in self.current_chain: self.current_chain.add(data.strike)

        current_rtm = None
        if len(data.five_sec_data) > 0: current_rtm = data.five_sec_data[0].rtm
        elif len(data.one_min_data) > 0: current_rtm = data.one_min_data[0].rtm
        elif len(data.tas) > 0: current_rtm = data.tas[0].current_rtm
        
        if data.right == "C":
            if data.strike not in self.tracked_calls.keys():
                sod = SingleOptionData(
                    symbol=data.symbol,
                    right=data.right,
                    current_rtm=data.five_sec_data[0].rtm,
                    strike=data.strike
                )
                self.tracked_calls[data.strike] = sod

            if (current_rtm is not None) and (current_rtm not in self.calls_by_rtm.keys()):
                sod_rtm = SingleOptionData(
                    symbol=data.symbol,
                    right=data.right,
                    current_rtm=current_rtm
                )
                self.calls_by_rtm[current_rtm] = sod_rtm
            
        if data.right == "P":
            if data.strike not in self.tracked_calls.keys():
                sod = SingleOptionData(
                    symbol=data.symbol,
                    right=data.right,
                    current_rtm=data.five_sec_data[0].rtm,
                    strike=data.strike
                )
                self.tracked_puts[data.strike] = sod

            if (current_rtm is not None) and (current_rtm not in self.puts_by_rtm.keys()):
                sod_rtm = SingleOptionData(
                    symbol=data.symbol,
                    right=data.right,
                    current_rtm=current_rtm
                )
                self.puts_by_rtm[current_rtm] = sod_rtm

        if len(data.ticks) > 0:
            ##########################################
            # TODO: Add function to send to websocket
            ##########################################
            return
        
        if len(data.five_sec_data) > 0:
            if data.right == "C":
                self.tracked_calls[data.strike].add_five_sec_data(data)
                self.calls_by_rtm[data.five_sec_data[0].rtm].add_five_sec_data(data)
            
            if data.right == "P":
                self.tracked_puts[data.strike].add_five_sec_data(data)
                self.puts_by_rtm[data.five_sec_data[0].rtm].add_five_sec_data(data)

        if len(data.one_min_data) > 0:
            if data.right == "C":
                self.tracked_calls[data.strike].add_one_min_data(data)
                self.calls_by_rtm[data.one_min_data[0].rtm].add_one_min_data(data)
            
            if data.right == "P":
                self.tracked_puts[data.strike].add_one_min_data(data)
                self.puts_by_rtm[data.one_min_data[0].rtm].add_one_min_data(data)

        if len(data.tas) > 0:
            return 


            

            





