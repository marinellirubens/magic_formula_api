import asyncio
import os
import time
import logging
import datetime

from flask import Flask, request, send_file
from flask_cors import CORS
import pandas
import numpy as np
from config import settings, parser
from databases import redis


app = Flask(__name__)
CORS(app)


@app.route('/', methods=['GET'])
async def get_stocks_info():
    start = time.perf_counter()
    roic_ignore = int(request.args.get('roic_ignore', 0))
    format = request.args.get('format', 'json').lower()

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
    if roic_ignore:
        tickers_df['roic_index_number'] = [0] * tickers_df['roic'].count()

    tickers_df = tickers_df.sort_values('earning_yield', ascending=False)

    tickers_df['earning_yield_index'] = np.arange(tickers_df['earning_yield'].count())
    tickers_df['magic_index'] = tickers_df['earning_yield_index'] + tickers_df['roic_index_number']

    tickers_df = tickers_df.sort_values('magic_index', ascending=True)
    if format == 'excel':
        filename = f'magic_formula_{datetime.datetime.now().strftime("%Y%m%d%H%M%S")}.xlsx'
        tickers_df.to_excel(
            filename,
            sheet_name='stocks', index=False, engine='openpyxl',
            freeze_panes=(1, 0)
        )
        file = send_file(filename)
        os.remove(filename)
        return file

    app.logger.info(f'Finished in {time.perf_counter() - start} seconds')
    tickers = tickers_df.to_dict(orient='records')
    return tickers


def main():
    credentials = parser.read_ini_file(settings.credentials_file_path)
    if not credentials:
        return
    settings.credentials = credentials

    app.logger.setLevel(logging.DEBUG)

    handler = logging.StreamHandler()
    handler.setLevel(logging.DEBUG)

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    app.logger.addHandler(handler)
    return app


if __name__ == '__main__':
    app.run()

