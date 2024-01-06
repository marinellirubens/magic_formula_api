import status_invest
import asyncio
import math
import pandas
import numpy as np
import time
from config.settings import use_cache


async def calculate_earning_yield(ticker_info):
    """ """
    try:
        ev_ebit = ticker_info.get('ev_ebit', 0)
        ev = ticker_info.get('Valor de firma', 0)
        print(ticker_info.get('ticker'), ev, ev_ebit)
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

    :return: Graham upside
    :rtype: float
    """
    if current_price <= 0 or graham_vi <= 0:
        return 0

    pre_vi = (graham_vi - current_price) / current_price

    return round(pre_vi, 2)


async def process_ticker_info(ticker_general):
    symbol = ticker_general.get('ticker', 'Not found')

    print(f'Processing ticker {symbol}')
    page = await status_invest.get_stocks_page_info(symbol)
    results = await status_invest.format_stock_page(page[1].content)
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
    return ticker_info


async def main():
    start = time.perf_counter()
    resp = await status_invest.get_stocks_info()
    # for item in resp.json():
        # results = await asyncio.gather(
            # get_stocks_historical_info(item.get('ticker')),
            # get_stocks_historical_price(item.get('ticker')),
            # get_stocks_page_info(item.get('ticker'))
        # )
        # break
    stocks_data = []
    tasks = []
    roic_ignore = True
    parallel_number = 6
    for ticker in resp.json():
        tasks.append(process_ticker_info(ticker))
        if len(tasks) > parallel_number and not use_cache:
            stocks_data += await asyncio.gather(*tasks)
            tasks = []
            time.sleep(0.1)

    if tasks:
        stocks_data += await asyncio.gather(*tasks)
    tickers_df = pandas.DataFrame(
        columns=['symbol', 'roic', 'vpa', 'lpa', 'p_l', 'p_vp', 'dividend_yield', 'current_price', 'earning_yield', 'graham_vi', 'graham_upside'],
        data=stocks_data
    )
    tickers_df.sort_values('roic', ascending=False)
    tickers_df['roic_index_number'] = np.arange(tickers_df['roic'].count())
    if roic_ignore:
        tickers_df['roic_index_number'] = [0] * tickers_df['roic'].count()
    tickers_df = tickers_df.sort_values('earning_yield', ascending=False)

    tickers_df['earning_yield_index'] = np.arange(tickers_df['earning_yield'].count())
    tickers_df['magic_index'] = tickers_df['earning_yield_index'] + tickers_df['roic_index_number']

    tickers_df = tickers_df.sort_values('magic_index', ascending=True)
    # tickers_df: pandas.DataFrame = tickers_df.loc[tickers_df['earning_yield'] > 0]
    # data_frame.loc[0] =ticker_info 
    tickers_df.to_excel(
        'teste.xlsx',
        sheet_name='stocks', index=False, engine='openpyxl',
        freeze_panes=(1, 0)
    )

    print(f'Finished in {time.perf_counter() - start} seconds')
    tickers = tickers_df.to_dict(orient='records')
    print(tickers)


if __name__ == '__main__':
    asyncio.run(main())

