import asyncio
import time

import pandas
import numpy as np
from config import settings, parser
from databases import redis



async def main():
    start = time.perf_counter()
    credentials = parser.read_ini_file(settings.credentials_file_path)
    if not credentials:
        return
    settings.credentials = credentials

    identifier = 'magic_formula_main_data'
    conn_info = redis.RedisConnectionInfo(
        settings.credentials['redis']['hostname'],
        settings.credentials['redis'].getint('port'),
        settings.credentials['redis']['password'],
    )
    stocks_data = await redis.get_object_from_redis_async(conn_info, identifier)
    tickers_df = pandas.DataFrame(
        columns=['symbol', 'roic', 'vpa', 'lpa', 'p_l', 'p_vp', 'dividend_yield', 'current_price', 'earning_yield', 'graham_vi', 'graham_upside'],
        data=stocks_data
    )
    tickers_df.sort_values('roic', ascending=False)
    tickers_df['roic_index_number'] = np.arange(tickers_df['roic'].count())
    roic_ignore = True
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
    # print(tickers)


if __name__ == '__main__':
    asyncio.run(main())

