"""Module to handle connections with postgres"""
import logging
import traceback
import time
from typing import Union, Any

import psycopg
# import psycopg_pool
from psycopg.abc import Query
from psycopg.rows import dict_row
# from urllib3.connection import connection

from config import logger
from config import parser, settings


async def create_connection_async(db_name: str, db_host: str, db_username: str,
                                  db_password: str, db_port: int) -> psycopg.AsyncConnection:
    """Creates an async connection with the postgres database

    Args:
        db_name(str): name of the database
        db_host(str): hostname of the machine
        db_username(str): username
        db_password(str): password
        db_port(int): database port

    Returns:
        returns a async connection to be used

    """
    logger.log_message(f"creating connection for database {db_name}, host {db_host}, user {db_username}, port {db_port}", level=logging.DEBUG)
    conn_info = psycopg.conninfo.make_conninfo(dbname=db_name, host=db_host,
                                               user=db_username, password=db_password, port=db_port)

    connection = await psycopg.AsyncConnection.connect(conn_info)
    return connection


async def read_query_async_with_connection(connection: psycopg.AsyncConnection, query: Query, params: Any = None) -> list:
    logger.log_message(f"Start of request to postgresql", level=logging.INFO)
    res = []
    request_start_time = time.time()
    try :
        cur = connection.cursor(row_factory=dict_row)
        await cur.execute(query, params=params)
        await connection.commit()

        res = await cur.fetchall()
        await cur.close()
    except Exception as error:
        logger.log_message(f'Error to get info from postgresql: {traceback.format_exc()}', level=logging.ERROR)
        res.append({'error': 1, 'desc': f'failed: {error}'})

    request_end_time = time.time()
    request_time = round(request_end_time - request_start_time, 2)
    logger.log_message(
        f"End of request to postgresql | RESPONSE TIME: {request_time} seconds, {len(res)} records returned",
        level=logging.INFO
    )

    return res


async def write_query_async_with_connection(connection: psycopg.AsyncConnection, query: Query, params: Any = None):
    """Writes informations on the database using a async connection.

    Args:
        connection (psycopg.AsyncConnection): Async connection to postgres
        query (Query): query to be used
        params(any): params to be used on the query

    Returns:
        returns a dictionary with the status of the operation

    """
    res = {}
    logger.log_message(f"Start of request to postgresql", level=logging.INFO)
    request_start_time = time.time()
    # conn, cur = None, None
    try :
        cur = connection.cursor(row_factory=dict_row)
        await cur.execute(query, params=params)
        await connection.commit()
        res = {'error':0, 'desc':'success'}
    except Exception as error:
        logger.log_message(f'Error to get info from postgresql: {traceback.format_exc()}', level=logging.ERROR)
        res = {'error': 1, 'desc': f'failed: {error}'}

    request_end_time = time.time()
    request_time = round(request_end_time - request_start_time, 2)
    logger.log_message(f"End of request to postgresql | RESPONSE TIME: {request_time} seconds", level=logging.INFO)
    return res


async def main_aync():
    credentials = parser.read_ini_file(settings.credentials_file_path)
    if not credentials:
        return

    connection = await create_connection_async(
        db_name=credentials['local_postgres']['database'],
        db_host=credentials['local_postgres']['hostname'],
        db_username=credentials['local_postgres']['user'],
        db_password=credentials['local_postgres']['password'],
        db_port=credentials['local_postgres'].getint('port'),
    )
    res = []
    try:
        res = await read_query_async_with_connection(connection, 'select 1 as teste')
    except Exception:
        if connection and not connection.closed:
            await connection.close()

    return res


async def get_info_from_database(base_query: Query, params: Any = None) -> list:
    """Gets the list of node from the database, for now the values are only an example

    Returns:
        returns a dict with the information retrieved from the database

    """
    credentials = settings.credentials
    if not credentials:
        credentials = parser.read_ini_file(settings.credentials_file_path)
        if not credentials:
            return []

        settings.credentials = credentials

    connection = await create_connection_async(
        db_name=credentials['local_postgres']['database'],
        db_host=credentials['local_postgres']['hostname'],
        db_username=credentials['local_postgres']['user'],
        db_password=credentials['local_postgres']['password'],
        db_port=credentials['local_postgres'].getint('port'),
    )

    res = []
    try:
        res = await read_query_async_with_connection(connection, base_query, params=params)
    except Exception:
        if connection and not connection.closed:
            await connection.close()

    if not res:
        return []

    return res


async def post_info_into_database(base_query: Query, params: Any = None) -> Union[list, dict]:
    """
    Post info on the database, for now the values are only an example
    """
    credentials = settings.credentials
    if not credentials:
        credentials = parser.read_ini_file(settings.credentials_file_path)
        if not credentials:
            return []

        settings.credentials = credentials

    connection = await create_connection_async(
        db_name=credentials['local_postgres']['database'],
        db_host=credentials['local_postgres']['hostname'],
        db_username=credentials['local_postgres']['user'],
        db_password=credentials['local_postgres']['password'],
        db_port=credentials['local_postgres'].getint('port'),
    )
    res = []
    try:
        res = await write_query_async_with_connection(connection, base_query, params=params)
    except Exception:
        if connection and not connection.closed:
            await connection.close()

    if not res:
        return []

    return res


if __name__ == '__main__':
    # asyncio.run(main_aync())
    main()
