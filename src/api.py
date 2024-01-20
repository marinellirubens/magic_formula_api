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
from status_invest import filter_stocks
import magic_formula
from swagger import swagger_blueprint, swagger_base_bp


app = Flask(__name__)
CORS(app)


def get_indexes_args():
    """Bovespa indexes
        (BRX100, IBOV, SMALL, IDIV, MLCX, IGCT, ITAG, IBRA, IGNM, IMAT, ALL)
        BRX100 - Indice IBRX100
        IBOV - IBOVESPA
        SMALL - Indice de Small Cap
        IDIV - Indice de Dividendos
        MLCX - Indice de Mid-Large Cap
        IGCT - Indice de Governança Corporativa
        ITAG - Indice de Ações com Tag Along diferenciado
        IBRA - Indice Brasil Amplo
        IGNM - Indice de Governança Corporativa - Novo Mercado
        IMAT - Indice de Materiais Basicos
        ALL - Todos os Indices anteriores

    Args:
        request:

    """
    indexes = request.args.getlist('indexes')
    app.logger.info(f'indexes: {indexes}')
    if not indexes or indexes == ['']:
        indexes = ['NONE', ]
    return indexes


def get_list_tickers_args():
    list_tickers = request.args.getlist('list_tickers', [])
    if list_tickers == ['']:
        list_tickers = []
    return list_tickers


@app.route('/api/magic_formula', methods=['GET'])
async def get_stocks_info():
    start = time.perf_counter()
    roic_ignore = int(request.args.get('roic_ignore', 0))
    indexes = get_indexes_args()
    format = request.args.get('format', 'json').lower()
    min_ebit = int(request.args.get('min_ebit', 1))
    min_market_cap = int(request.args.get('min_market_cap', 0))
    number_of_stocks = int(request.args.get('number_of_stocks', 150))
    graham_max_pl = float(request.args.get('graham_max_pl', 15))
    graham_max_pvp = float(request.args.get('graham_max_pvp', 1.5))
    list_tickers = get_list_tickers_args()

    identifier = 'magic_formula_main_data'
    conn_info = redis.RedisConnectionInfo(
        settings.credentials['redis']['hostname'],
        settings.credentials['redis'].getint('port'),
        settings.credentials['redis']['password'],
    )

    stocks_data = await redis.get_object_from_redis_async(conn_info, identifier)
    stocks_data = await filter_stocks(stocks_data, indexes, list_tickers,
                                      min_ebit, min_market_cap, app.logger)
    if graham_max_pl != 15 or graham_max_pvp != 1.5:
        for stock in stocks_data:
            stock['graham_vi'] = await magic_formula.calculate_graham_vi(
                stock['vpa'], stock['lpa'], graham_max_pl, graham_max_pvp
            )
            stock['graham_upside'] = await magic_formula.calculate_graham_upside(
                stock['current_price'], stock['graham_vi']
            )

    tickers_df = pandas.DataFrame(
        columns=['symbol', 'roic', 'vpa', 'lpa', 'p_l', 'p_vp', 'dividend_yield',
                 'current_price', 'earning_yield', 'graham_vi', 'graham_upside',
                 'ebit', 'market_cap'],
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

    if number_of_stocks:
        tickers_df = tickers_df.head(number_of_stocks)

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

    app.register_blueprint(swagger_blueprint)
    app.register_blueprint(swagger_base_bp)
    return app


if __name__ == '__main__':
    app = main()
    app.run('0.0.0.0', port=5001)

