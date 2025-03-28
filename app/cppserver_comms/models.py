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

    @classmethod
    def random(cls):
        timestamp = int(time.time() * 1000)  # Current timestamp in milliseconds
        price = round(random.uniform(0.05, 50.0), 2)  # Random price between 0.05 and 50
        quantity = random.randint(1, 25)  # Quantity between 1 and 25
        total_volume = random.randint(5000, 60000)  # Total volume between 5000 and 60000
        vwap = round(random.uniform(1, 40), 3)  # VWAP between 1 and 40
        
        current_ask = round(random.uniform(price, price + 5), 2) if random.random() > 0.1 else price-0.1
        current_bid = round(random.uniform(price - 5, price), 2) if random.random() > 0.1 else price+0.1
        current_rtm = random.choice(["ITM1", "ITM2", "ITM3", "OTM1", "OTM2", "OTM3", "OTM4", "ITM4", "ITM5", "OTM5"])
        
        return cls(
            timestamp=timestamp,
            price=price,
            quantity=quantity,
            total_volume=total_volume,
            vwap=vwap,
            current_ask=current_ask,
            current_bid=current_bid,
            current_rtm=current_rtm,
        )

class TimeAndSalesAggregated(BaseModel):
    timestamp: int
    volume_at_ask: int
    total_value_at_ask: float
    otm_volume_at_ask: int
    itm_volume_at_ask: int
    volume_at_bid: int
    total_value_at_bid: float
    otm_volume_at_bid: int
    itm_volume_at_bid: int
    volume_at_middle: int
    total_value_at_middle: float
    otm_volume_at_middle: int
    itm_volume_at_middle: int

class TimeAndSalesByMinute(BaseModel):
    ticker: str
    call_data: List[TimeAndSalesAggregated]
    put_data: List[TimeAndSalesAggregated]

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

    @classmethod
    def random(cls):
        return cls(
            symbol="SPX",
            strike=random.choice(range(6000, 6100, 5)),
            right=random.choice(["C", "P"]),
            exp_date="",
            ticks=[],
            five_sec_data=[],
            one_min_data=[],
            tas=[TimeAndSalesDataModel.random()]
        )
    

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
    
    @classmethod
    def random_candles(cls, open, high, low, close, max_price, min_price):
        def get_time_stamp():
            current_time = time.time()
            even_minute_time = round(current_time / 60) * 60
            # Subtract 60 so that candle appears to be created prior to first tick
            return even_minute_time - 60
        
        return cls(
            symbol="SPX",
            underlying_one_min=[
                UnderlyingOneMinDataModel(
                    time=get_time_stamp(),
                    date_time=datetime.fromtimestamp(round(time.time())),
                    open=open,
                    high=high,
                    low=low,
                    close=close,
                    volume=0,
                    daily_high=max_price,
                    daily_low=min_price,
                    daily_volume=0,
                    total_call_volume=random.randint(100000,150000),
                    total_put_volume=random.randint(100000,150000),
                    index_future_premium=random.uniform(0.1,2.0),
                    total_trade_count=0,
                    one_minute_trade_rate=0,
                    rt_historical_volatility=0,
                    option_implied_volatility=random.uniform(0.0,1.0),
                    call_open_interest=random.uniform(100000, 150000),
                    put_open_interest=random.uniform(100000,150000),
                    futures_open_interest=0
                )
            ],
            underlying_averages=[],
            underlying_price_ticks=[]
        )


class NewsEventModel(BaseModel):
    time: int
    date_time: datetime
    article_id: str
    headline: str
    sentiment_score: float

    # Random data generation
    # @classmethod
    # def random(cls):
    #     def random_datetime():
    #         return datetime.now() - timedelta(seconds=random.randint(0, 100000))
        
    #     return cls(
    #         time=int((datetime.now() - timedelta(seconds=random.randint(0, 100000))).timestamp() * 1000),
    #         date_time=random_datetime(),
    #         article_id=f"ART{random.randint(1000, 9999)}",
    #         headline=f"Breaking News {random.randint(1, 100)}",
    #         sentiment_score=random.uniform(-1, 1)
    #     )


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


########################################################################################
# Outbound Websocket Models
########################################################################################

# Underlying

class UnderlyingCandle(BaseModel):
    time: int
    open: float
    high: float
    low: float
    close: float
    total_call_volume: Optional[int]
    total_put_volume: Optional[int]
    option_implied_volatility: Optional[float]
    candle_returns: Optional[float] = 0
    call_volume_delta: Optional[float] = 0
    put_volume_delta: Optional[float] = 0

class UnderlyingTick(BaseModel):
    time: int
    price: float

class UnderlyingExtraData(BaseModel):
    call_open_interest: int
    put_open_interest: int
    futures_open_interest: int
    low_13_week: float
    high_13_week: float 
    low_26_week: float
    high_26_week: float
    low_52_week: float
    high_52_weeK: float
    daily_high: float
    daily_low: float
    last_option_iv: float

class UnderlyingGeneral(BaseModel):
    symbol: str
    candle: Optional[UnderlyingCandle] = None
    tick: Optional[UnderlyingTick] = None
    extra_data: Optional[UnderlyingExtraData] = None

# Real Time Trade Feed

class TimeAndSales(BaseModel):
    timestamp: int
    symbol: str
    right: str
    strike: int
    price: float
    quantity: int
    total_cost: float
    total_volume: int
    vwap: float
    current_ask: Optional[float]
    current_bid: Optional[float]
    current_rtm: Optional[str]

def filter_tas_data(
    data: List[TimeAndSales],
    right: str,
    rtm: str,
    quantity: int,
    cost: float,
    limit: int
) -> List[TimeAndSales]:
    
    right_filter = None
    if right == "CALLS":
        right_filter = "C"
    elif right == "PUTS":
        right_filter = "P"

    strike_filter = None
    if rtm in ["ITM", "OTM"]:
        strike_filter = rtm

    quantity_ranges = {
        0: (0, float("inf")),
        5: (5, float("inf")),
        10: (10, float("inf")),
        25: (25, float("inf")),
        50: (50, float("inf")),
        100: (100, float("inf")),
        250: (250, float("inf")),
        500: (500, float("inf")),
        1000: (1000, float("inf")),
    }
    quantity_start, quantity_end = quantity_ranges.get(quantity, (None, None))

    cost_ranges = {
        0: (0.00, float("inf")),
        1000: (1000.00, float("inf")),
        5000: (5000.00, float("inf")),
        10000: (10000.00, float("inf")),
        25000: (25000.00, float("inf")),
        50000: (50000.00, float("inf")),
        100000: (100000.00, float("inf")),
        1000000: (1000000.00, float("inf")),
    }
    cost_start, cost_end = cost_ranges.get(cost, (None, None))

    filtered_data = []
    for item in data:
        if right_filter and item.right != right_filter:
            continue
        if strike_filter and not (item.current_rtm and strike_filter in item.current_rtm):
            continue
        if quantity_start is not None and not (quantity_start <= item.quantity <= quantity_end):
            continue
        if cost_start is not None and not (cost_start <= item.total_cost <= cost_end):
            continue
        filtered_data.append(item)

    # Sort by timestamp (most recent first) and limit results
    filtered_data.sort(key=lambda x: x.timestamp, reverse=True)
    return filtered_data[:limit]


# General

class OutboundWSData(BaseModel):
    type: str # underlying, news, option, or tas
    news: Optional[NewsEventModel] = None
    underlying: Optional[UnderlyingGeneral] = None
    option: Optional[OptionDataModel] = None
    tas: Optional[TimeAndSales] = None