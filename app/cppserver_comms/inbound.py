import asyncio
from proto import messages_pb2 
from utils.singleton import Singleton
from app.cppserver_comms.models import (BasicMessageModel, ConfirmationModel, ISBActionModel, 
                                        OptionDataModel, FiveSecDataModel, TimeAndSalesDataModel,
                                        UnderlyingOneMinDataModel, UnderlyingAveragesModel,
                                        TickDataModel, OneMinDataModel, UnderlyingPriceTickModel,
                                        UnderlyingContractModel, NewsEventModel)
from pydantic import ValidationError
from google.protobuf.message import Message as ProtobufMessage
from typing import Union
from datetime import datetime

from app.market_data_handling import hf_data_processor

hf_data = hf_data_processor.HFDataHandler()

# Handle all incoming messages from the CPP Server here
class WSDataHandler(metaclass=Singleton):
    def __init__(self):
        self.message_queue = asyncio.Queue()

    async def start(self):
        asyncio.create_task(self.process_ws_messages())

    async def receive_ws_message(self, message):
        await self.message_queue.put(message)

    async def process_ws_messages(self):
        while True:
            try:
                message = await self.message_queue.get()
                parsed_message = messages_pb2.Message()
                parsed_message.ParseFromString(message)
                # print(f"Received message: {parsed_message}")

                pydantic_model = self.convert_from_protobuf(protobuf_message=parsed_message)
                await self.handle_formatted_messages(pydantic_model=pydantic_model)
            except Exception as e:
                print(f"Exception thrown during cpp websocket processing: {e}")
                continue    

    def convert_from_protobuf(self, protobuf_message) -> Union[BasicMessageModel, ConfirmationModel, 
                                                               ISBActionModel, OptionDataModel, UnderlyingContractModel,
                                                               UnderlyingPriceTickModel, NewsEventModel]:
        """
        Convert a Protobuf message to a Pydantic model using hardcoded mappings.
        """
        message_type = protobuf_message.type

        if message_type == "basic_message":
            return BasicMessageModel(message=protobuf_message.basic_message.message)

        elif message_type == "confirmation":
            return ConfirmationModel(
                action=protobuf_message.confirmation.action,
                status=protobuf_message.confirmation.status,
            )

        elif message_type == "isb_action":
            return ISBActionModel(
                component=protobuf_message.isb_action.component,
                action=protobuf_message.isb_action.action,
                data=protobuf_message.isb_action.data,
            )

        elif message_type == "option_data":
            # Hardcode mapping for OptionDataModel
            return OptionDataModel(
                symbol=protobuf_message.option_data.symbol,
                strike=protobuf_message.option_data.strike,
                right=protobuf_message.option_data.right,
                exp_date=protobuf_message.option_data.exp_date,
                ticks=[
                    TickDataModel(
                        timestamp=tick.timestamp,
                        bid_price=tick.bid_price,
                        bid_size=tick.bid_size,
                        ask_price=tick.ask_price,
                        ask_size=tick.ask_size,
                        last_price=tick.last_price,
                        mark_price=tick.mark_price,
                        volume=tick.volume,
                        implied_vol=tick.implied_vol,
                        delta=tick.delta,
                        gamma=tick.gamma,
                        vega=tick.vega,
                        theta=tick.theta
                    )
                    for tick in protobuf_message.option_data.ticks
                ],
                five_sec_data=[
                    FiveSecDataModel(
                        time=fsd.time,
                        open=fsd.open,
                        close=fsd.close,
                        high=fsd.high,
                        low=fsd.low,
                        volume=fsd.volume,
                        count=fsd.count,
                        rtm=fsd.rtm,
                    )
                    for fsd in protobuf_message.option_data.five_sec_data
                ],
                one_min_data=[
                    OneMinDataModel(
                        time=omd.time,
                        open=omd.open,
                        close=omd.close,
                        high=omd.high,
                        low=omd.low,
                        candle_vol=omd.candle_vol,
                        trade_count=omd.trade_count,
                        implied_vol=omd.implied_vol,
                        delta=omd.delta,
                        gamma=omd.gamma,
                        vega=omd.vega,
                        theta=omd.theta,
                        und_price=omd.und_price,
                        total_vol=omd.total_vol,
                        rtm=omd.rtm
                    )
                    for omd in protobuf_message.option_data.one_min_data
                ],
                tas=[
                    TimeAndSalesDataModel(
                        timestamp=tas.timestamp,
                        price=tas.price,
                        quantity=tas.quantity,
                        total_volume=tas.total_volume,
                        vwap=tas.vwap,
                        current_ask=tas.current_ask,
                        current_bid=tas.current_bid,
                        current_rtm=tas.current_rtm,
                    )
                    for tas in protobuf_message.option_data.tas
                ],
            )

        elif message_type == "underlying_contract":
            return UnderlyingContractModel(
                symbol=protobuf_message.underlying_contract.symbol,
                underlying_price_ticks=[
                    UnderlyingPriceTickModel(
                        time=upt.time,
                        price=upt.price
                    )
                    for upt in protobuf_message.underlying_contract.underlying_price_tick
                ],
                underlying_one_min=[
                    UnderlyingOneMinDataModel(
                        time=uom.time,
                        date_time=datetime.fromtimestamp(uom.time),
                        open=uom.open,
                        high=uom.high,
                        low=uom.low,
                        close=uom.close,
                        volume=uom.volume,
                        daily_high=uom.daily_high,
                        daily_low=uom.daily_low,
                        daily_volume=uom.daily_volume,
                        total_call_volume=uom.total_call_volume,
                        total_put_volume=uom.total_put_volume,
                        index_future_premium=uom.index_future_premium,
                        total_trade_count=uom.total_trade_count,
                        one_minute_trade_rate=uom.one_minute_trade_rate,
                        rt_historical_volatility=uom.real_time_historical_volatility,
                        option_implied_volatility=uom.option_implied_volatility,
                        call_open_interest=uom.call_open_interest,
                        put_open_interest=uom.put_open_interest,
                        futures_open_interest=uom.futures_open_interest
                    )
                    for uom in protobuf_message.underlying_contract.underlying_one_min
                ],
                underlying_averages=[
                    UnderlyingAveragesModel(
                        low_13_week=ua.low_13_week,
                        high_13_week=ua.high_13_week,
                        low_26_week=ua.low_26_week,
                        high_26_week=ua.high_26_week,
                        low_52_week=ua.low_52_week,
                        high_52_weeK=ua.high_52_week,
                        average_volume_90_day=ua.average_volume_90_day
                    )
                    for ua in protobuf_message.underlying_contract.underlying_averages
                ]
            )
        
        elif message_type == "news":
            return NewsEventModel(
                time=protobuf_message.news.time,
                date_time=datetime.fromtimestamp(protobuf_message.news.time / 1000),
                article_id=protobuf_message.news.article_id,
                headline=protobuf_message.news.headline,
                sentiment_score=protobuf_message.news.sentiment_score
            )

        else:
            raise ValueError(f"Unsupported message type: {message_type}")
    
    async def handle_formatted_messages(self, pydantic_model):
        """
        Perform actions based on the type of the Pydantic model.
        """
        if isinstance(pydantic_model, BasicMessageModel):
            print(f"Received basic message: {pydantic_model.message}")

        elif isinstance(pydantic_model, ConfirmationModel):
            print(f"Received confirmation message.")
            print(f"Action: {pydantic_model.action}")
            print(f"Status: {pydantic_model.status}")

        elif isinstance(pydantic_model, ISBActionModel):
            print(f"Received ISB Action message.")
            print(f"Component: {pydantic_model.component}")
            print(f"Action: {pydantic_model.action}")
            print(f"Data: {pydantic_model.data}")

        elif isinstance(pydantic_model, OptionDataModel):
            await hf_data.add_new_data(pydantic_model=pydantic_model)
        
        elif isinstance(pydantic_model, UnderlyingContractModel):
            await hf_data.add_new_data(pydantic_model=pydantic_model)

        elif isinstance(pydantic_model, NewsEventModel):
            await hf_data.add_new_data(pydantic_model=pydantic_model)
            print(f"Article Received: {pydantic_model.headline}")
            print(f"Sentiment Score: {pydantic_model.sentiment_score}")
            print(f"Time: {pydantic_model.date_time}")

        else:
            print("Unhandled message type.")
