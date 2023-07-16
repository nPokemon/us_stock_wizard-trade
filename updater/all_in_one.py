"""
Please Exec it after market close on trading day
0. Get tickers
1. Trading Calendar
2. Get earning call
4. Get Fundamental
3. Get Kline
5. Get RS

--
Run screening.
"""

import asyncio
import logging
import pandas as pd
from us_stock_wizard.database.db_utils import StockDbUtils, DbTable
from us_stock_wizard.src.stocks import StockTickers
from us_stock_wizard.src.stocks import TradingCalendar
from us_stock_wizard.src.fundamentals import Fundamentals
from us_stock_wizard.src.kline import KlineFetch
from us_stock_wizard.screener.rs_calculator import RelativeStrengthCalculator


async def check_trading_day() -> bool:
    """
    Check if today is a trading day
    """
    cal = await StockDbUtils.read(DbTable.TRADING_CALENDAR, output="df")
    cal["date"] = pd.to_datetime(cal["date"]).dt.date
    # check today in cal["date"]
    today = pd.Timestamp.today().date()
    is_today_trading = today in cal["date"].tolist()
    if not is_today_trading:
        logging.info("Today is not a trading day, skip")
        return False
    return True


async def get_tickers():
    st = StockTickers()
    await st.handle_all_tickers()
    logging.info("Done Ticker")


async def get_calendar():
    tc = TradingCalendar()
    await tc.handle_calendar()
    logging.info("Done Calendar")


async def get_earning_call_fundamentals():
    fundamentals = Fundamentals()
    await fundamentals.handle_earning_call_data()
    await fundamentals.update_is_data(days_ago=5)
    logging.info("Done Earning Call and Fundamental")


async def get_kline():
    kf = KlineFetch()
    await kf.initialize()
    await kf.update_all_tickers()
    logging.info("Done Kline")


async def get_rs():
    rs = RelativeStrengthCalculator()
    await rs.initialize()
    await rs.update_all_rs()


async def main():
    is_trading_day = await check_trading_day()
    if not is_trading_day:
        return
    await get_tickers()
    await get_calendar()
    await get_earning_call_fundamentals()
    await get_kline()
    await get_rs()


if __name__ == "__main__":
    asyncio.run(main())
