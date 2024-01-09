import asyncio
import math
import time
import logging

from config import settings, parser
from databases import redis
import status_invest


logger = logging.getLogger('magic_formula')
logger.setLevel(logging.DEBUG)

handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


async def calculate_earning_yield(ticker_info: dict) -> float:
    """Calculate earning yield based on ticker info

    Args:
        ticker_info (dict): dictionary with the information on the ticker

    Returns:
        returns the value of the earning yield in percentage, if error returns 0

    """
    try:
        ev_ebit = ticker_info.get('ev_ebit', 0)
        ev = ticker_info.get('Valor de firma', 0)
        # logging.info(ticker_info.get('ticker'), ev, ev_ebit)
        ebit = ev / ev_ebit
        earning_yield = round(ebit / ev, 2)
    except ZeroDivisionError:
        return 0

    return earning_yield


async def calculate_graham_vi(
        vpa: float,
        lpa: float,
        max_p_l: float = 15,
        max_p_vp: float = 1.5) -> float:
    """Calculates the Graham VI.

    :return: Graham VI
    :rtype: float
    """
    if vpa <= 0 or lpa <= 0:
        return 0

    pre_vi = (max_p_l * max_p_vp) * vpa * lpa

    try:
        graham_vi = math.sqrt(pre_vi)
    except ValueError:
        graham_vi = 0

    return round(graham_vi, 2)


async def calculate_graham_upside(
        current_price: float,
        graham_vi: float) -> float:
    """Calculates the Graham upside based on the calculated VI

    Args:
        current_price (float): current stock price
        graham_vi (float): intrinsic value calculated using graham method

    Returns(float):
        Graham upside

    """
    if current_price <= 0 or graham_vi <= 0:
        return 0

    pre_vi = (graham_vi - current_price) / current_price

    return round(pre_vi, 2)


async def process_ticker_info(ticker_general: dict) -> list:
    """Process the information on the ticker and return the relevant fields

    Args:
        ticker_general (dict): ticker information collected on status invest

    Returns:
        returns a list with the fields calculated for the ticker

    """
    symbol = ticker_general.get('ticker', 'Not found')

    logger.info(f'Starting process for ticker {symbol}')
    page = await status_invest.get_stocks_page_info(symbol)
    results = await status_invest.format_stock_page(page[1].content, logger)
    ticker_general.update(results)

    roic = ticker_general.get('roic', 0)
    vpa = ticker_general.get('vpa', 0)
    lpa = ticker_general.get('lpa', 0)
    p_l = ticker_general.get('p_l', 0)
    p_vp = ticker_general.get('p_vp', 0)
    dividend_yield = ticker_general.get('dy', 0)
    current_price = ticker_general.get('price', 0)
    ey = await calculate_earning_yield(ticker_general)
    graham_vi = await calculate_graham_vi(vpa, lpa)
    graham_upside = await calculate_graham_upside(current_price, graham_vi)

    ticker_info = [
        symbol,
        roic,
        vpa,
        lpa,
        p_l,
        p_vp,
        dividend_yield,
        current_price,
        ey,
        graham_vi,
        graham_upside
    ]
    logger.info(f'Finishing process for ticker {symbol}')
    return ticker_info


async def main():
    logger.info('Starting process')
    identifier = 'magic_formula_main_data'

    credentials = parser.read_ini_file(settings.credentials_file_path)
    if not credentials:
        return
    settings.credentials = credentials

    conn_info = redis.RedisConnectionInfo(
        settings.credentials['redis']['hostname'],
        settings.credentials['redis'].getint('port'),
        settings.credentials['redis']['password'],
    )

    while True:
        stocks_data = []
        tasks = []

        logger.info('Processing stock information')
        resp = await status_invest.get_stocks_info()
        for ticker in resp.json().get('list', []):
            tasks.append(process_ticker_info(ticker))
            if len(tasks) > settings.parallel_number_requests and not settings.use_cache:
                stocks_data += await asyncio.gather(*tasks)
                tasks = []
                time.sleep(0.1)

        if tasks:
            stocks_data += await asyncio.gather(*tasks)

        logger.info('writing into redis')
        await redis.set_object_on_redis_async(conn_info, identifier, stocks_data, time_to_live=None)

        logger.info('Waiting for next itteration')
        time.sleep(settings.time_to_sleep_minutes * 60)


if __name__ == '__main__':
    asyncio.run(main())

