from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timedelta
import random
import time

class BasicMessageModel(BaseModel):
    message: str

class ConfirmationModel(BaseModel):
    action: str
    status: str

class ISBActionModel(BaseModel):
    component: str
    action: str
    data: Optional[str] = None


###################################################################
# Sub models of option ticks to be sent via websocket to front end
###################################################################

class BidPrice(BaseModel):
    timestamp: int
    bid_price: float

class TimeAndSalesDataModel(BaseModel):
    timestamp: int
    price: float
    quantity: int
    total_volume: int
    vwap: float
    current_ask: Optional[float]
    current_bid: Optional[float]
    current_rtm: Optional[str]

class TickDataModel(BaseModel):
    timestamp: int
    bid_price: Optional[float]
    bid_size: Optional[float]
    ask_price: Optional[float]
    ask_size: Optional[float]
    last_price: Optional[float]
    mark_price: Optional[float]
    volume: Optional[float]
    implied_vol: Optional[float]
    delta: Optional[float]
    gamma: Optional[float]
    vega: Optional[float]
    theta: Optional[float]

class FiveSecDataModel(BaseModel):
    time: int
    open: float
    close: float
    high: float
    low: float
    volume: Optional[str]
    count: Optional[int]
    rtm: Optional[str]

class OneMinDataModel(BaseModel):
    time: int 
    open: float
    close: float
    high: float
    low: float
    candle_vol: float
    trade_count: Optional[float]
    implied_vol: Optional[float]
    delta: Optional[float]
    gamma: Optional[float]
    vega: Optional[float]
    theta: Optional[float]
    und_price: float
    total_vol: float
    rtm: Optional[str]

class OptionDataModel(BaseModel):
    symbol: str
    strike: int
    right: str
    exp_date: str
    ticks: Optional[List[TickDataModel]]
    five_sec_data: Optional[List[FiveSecDataModel]]
    one_min_data: Optional[List[OneMinDataModel]]
    tas: Optional[List[TimeAndSalesDataModel]]

class UnderlyingPriceTickModel(BaseModel):
    time: int
    price: float

class UnderlyingOneMinDataModel(BaseModel):
    time: int
    date_time: datetime
    open: float
    high: float
    low: float
    close: float
    volume: Optional[int]
    daily_high: Optional[float]
    daily_low: Optional[float]
    daily_volume: Optional[int]
    total_call_volume: Optional[int]
    total_put_volume: Optional[int]
    index_future_premium: Optional[float]
    total_trade_count: Optional[int]
    one_minute_trade_rate: Optional[float]
    rt_historical_volatility: Optional[float]
    option_implied_volatility: Optional[float]
    call_open_interest: Optional[float]
    put_open_interest: Optional[float]
    futures_open_interest: Optional[float]

class UnderlyingAveragesModel(BaseModel):
    low_13_week: float
    high_13_week: float
    low_26_week: float
    high_26_week: float
    low_52_week: float
    high_52_weeK: float
    average_volume_90_day: Optional[float]

class UnderlyingContractModel(BaseModel):
    symbol: str
    underlying_one_min: Optional[List[UnderlyingOneMinDataModel]]
    underlying_averages: Optional[List[UnderlyingAveragesModel]]
    underlying_price_ticks: Optional[List[UnderlyingPriceTickModel]]

    # Random data generation
    @classmethod
    def random_tick(cls, prev):   
        #previous_price = 5970 # Starting price to generate random values based off of

        def next_price(prev):
            return round(prev + random.uniform(-1, 1), 2)
        
        return cls(
            symbol="SPX",
            underlying_one_min=[],
            underlying_averages=[],
            underlying_price_ticks=[
                UnderlyingPriceTickModel(
                    time=round(time.time() * 1000),
                    price=next_price(prev=prev)
                )
            ]
        )

class NewsEventModel(BaseModel):
    time: int
    date_time: datetime
    article_id: str
    headline: str
    sentiment_score: float

    # Random data generation
    @classmethod
    def random(cls):
        def random_datetime():
            return datetime.now() - timedelta(seconds=random.randint(0, 100000))
        
        return cls(
            time=int((datetime.now() - timedelta(seconds=random.randint(0, 100000))).timestamp() * 1000),
            date_time=random_datetime(),
            article_id=f"ART{random.randint(1000, 9999)}",
            headline=f"Breaking News {random.randint(1, 100)}",
            sentiment_score=random.uniform(-1, 1)
        )


class MessageModel(BaseModel):
    type: str
    basic_message: Optional[BasicMessageModel] = None
    confirmation: Optional[ConfirmationModel] = None
    isb_action: Optional[ISBActionModel] = None
    option_data: Optional[OptionDataModel] = None

MESSAGE_TYPE_MAP = {
    "basic_message": BasicMessageModel,
    "confirmation": ConfirmationModel,
    "isb_action": ISBActionModel,
    "option_data": OptionDataModel
}