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
from datetime import datetime, timedelta
from typing import Optional, List

from utils.standard_dev import StreamingStatistics
from app.cppserver_comms.models import (OptionDataModel, TimeAndSalesDataModel, TimeAndSalesByMinute,
                                        FiveSecDataModel, OneMinDataModel, TimeAndSalesAggregated)

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

        self.calls_tas_aggregated: List[TimeAndSalesAggregated] = []
        self.puts_tas_aggregated: List[TimeAndSalesAggregated] = []
        self.tas_by_minute = TimeAndSalesByMinute(
            ticker=symbol,
            call_data=self.calls_tas_aggregated,
            put_data=self.puts_tas_aggregated
        )

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
                    current_rtm=current_rtm,
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
            if data.strike not in self.tracked_puts.keys():
                sod = SingleOptionData(
                    symbol=data.symbol,
                    right=data.right,
                    current_rtm=current_rtm,
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
            trade = data.tas[0]
            # print(f"{trade.timestamp} | Trade Price: {trade.price} | Amount: {trade.quantity} | Total Vol: {trade.total_volume} | Current RTM: {trade.current_rtm} | Bid: {trade.current_bid} | Ask: {trade.current_ask}")

            if data.right == "C":
                self.update_time_and_sales_aggregate_data(trade=trade, tas_aggregated=self.tas_by_minute.call_data)
            elif data.right == "P":
                self.update_time_and_sales_aggregate_data(trade=trade, tas_aggregated=self.tas_by_minute.put_data)
            else:
                print("Invalid option right during data intake.")

    def get_tas_aggregate_data(self): return self.tas_by_minute

    def update_time_and_sales_aggregate_data(self, trade: TimeAndSalesDataModel, tas_aggregated: List[TimeAndSalesAggregated]):
        if len(tas_aggregated) > 0:
            time = tas_aggregated[-1].timestamp

            if trade.timestamp < ((time + 60) * 1000):
                if trade.price >= trade.current_ask:
                    tas_aggregated[-1].volume_at_ask += trade.quantity
                    tas_aggregated[-1].total_value_at_ask += round(float(trade.quantity) * trade.price, 2)
                    
                    if "OTM" in trade.current_rtm: tas_aggregated[-1].otm_volume_at_ask += trade.quantity
                    if "ITM" in trade.current_rtm: tas_aggregated[-1].itm_volume_at_ask += trade.quantity

                elif trade.price <= trade.current_bid:
                    tas_aggregated[-1].volume_at_bid += trade.quantity
                    tas_aggregated[-1].total_value_at_bid += round(float(trade.quantity) * trade.price, 2)

                    if "OTM" in trade.current_rtm: tas_aggregated[-1].otm_volume_at_bid += trade.quantity
                    if "ITM" in trade.current_rtm: tas_aggregated[-1].itm_volume_at_bid += trade.quantity

                else:
                    tas_aggregated[-1].volume_at_middle += trade.quantity
                    tas_aggregated[-1].total_value_at_middle += round(float(trade.quantity) * trade.price, 2)
            
                    if "OTM" in trade.current_rtm: tas_aggregated[-1].otm_volume_at_middle += trade.quantity
                    if "ITM" in trade.current_rtm: tas_aggregated[-1].itm_volume_at_middle += trade.quantity

            else:
                tas_one_minute = self.create_time_and_sales_aggregate_data(time=time+60, trade=trade)
                tas_aggregated.append(tas_one_minute)

        else:
            # Get the timestamp of the most recent minute
            now = datetime.now()
            recent_minute = now.replace(second=0, microsecond=0)
            recent_minute_unix = int(recent_minute.timestamp())

            tas_one_minute = self.create_time_and_sales_aggregate_data(time=recent_minute_unix, trade=trade)
            tas_aggregated.append(tas_one_minute)
            
    def create_time_and_sales_aggregate_data(self, time, trade: TimeAndSalesDataModel):
        volume_at_ask = 0
        total_value_at_ask = 0.0
        volume_at_bid = 0
        total_value_at_bid = 0.0
        volume_at_middle = 0
        total_value_at_middle = 0.0
        otm_volume_at_ask = 0
        itm_volume_at_ask = 0
        otm_volume_at_bid = 0
        itm_volume_at_bid = 0
        otm_volume_at_middle = 0
        itm_volume_at_middle = 0

        if trade.price >= trade.current_ask:
            volume_at_ask = trade.quantity
            total_value_at_ask = round(float(trade.quantity) * trade.price, 2)

            if "OTM" in trade.current_rtm: otm_volume_at_ask += trade.quantity
            if "ITM" in trade.current_rtm: itm_volume_at_ask += trade.quantity
        elif trade.price <= trade.current_bid:
            volume_at_bid = trade.quantity
            total_value_at_bid = round(float(trade.quantity) * trade.price, 2)

            if "OTM" in trade.current_rtm: otm_volume_at_bid += trade.quantity
            if "ITM" in trade.current_rtm: itm_volume_at_bid += trade.quantity
        else:
            volume_at_middle = trade.quantity
            total_value_at_middle = round(float(trade.quantity) * trade.price, 2)

            if "OTM" in trade.current_rtm: otm_volume_at_middle += trade.quantity
            if "ITM" in trade.current_rtm: itm_volume_at_middle += trade.quantity
        
        tas_single_minute = TimeAndSalesAggregated(
            timestamp=time,
            volume_at_ask=volume_at_ask,
            total_value_at_ask=total_value_at_ask,
            otm_volume_at_ask=otm_volume_at_ask,
            itm_volume_at_ask=itm_volume_at_ask,
            volume_at_bid=volume_at_bid,
            total_value_at_bid=total_value_at_bid,
            otm_volume_at_bid=otm_volume_at_bid,
            itm_volume_at_bid=itm_volume_at_bid,
            volume_at_middle=volume_at_middle,
            total_value_at_middle=total_value_at_middle,
            otm_volume_at_middle=otm_volume_at_middle,
            itm_volume_at_middle=itm_volume_at_middle
        )

        return tas_single_minute
            





