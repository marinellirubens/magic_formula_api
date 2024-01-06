
"""Module with some basic implementation of the redis connection"""
import asyncio
import logging
import traceback
import simplejson
import pickle

import redis.asyncio as redis_async
from redis.asyncio import Redis

from typing import Union
from dataclasses import dataclass

from config import parser
from config import logger
from config import settings


@dataclass
class RedisConnectionInfo:
    """Class to hold the connection info for oracle database"""
    hostname: str
    port: int
    password: str = ''

    def __repr__(self) -> str:
        return f"{self.hostname}:{self.port}"


async def get_redis_connection_async(
        connection_info: RedisConnectionInfo = None,
        host: str = '',
        port: int = None,
        password: str = '') -> Union[None, Redis[bytes]]:
    """Creates a connection pool if does not exists and return a connection from this pool

    Args:
        connection_info (RedisConnectionInfo): Object with the connection info, if this is informed the other fields does not need to be informed
        host (str): host of redis instance
        port (int): port for redis instance
        password (str): password for the connection if needed

    Returns:
        returns a redis connection

    Raises:
        Exception:
            if no parameter is informed a exception if raised.
    """

    if not any([connection_info, host, port, password]):
        raise Exception('The connection information should be informed')

    if connection_info:
        host = connection_info.hostname
        port = connection_info.port
        password = connection_info.password

    try:
        redis_conn = await redis_async.Redis(
            host=host,
            port=port,
            password=password
        )

        await redis_conn.ping()
    except:
        logger.log_message(message=f"Error trying to connect to redis: {traceback.print_exc()}", level=logging.ERROR)
        return None

    return redis_conn


async def write_object_into_redis_async(key: str, object_to_save: Union[dict, str, bytes], redis_conn, time_to_live=300) -> bool:
    """Writes a dict into redis as a string

    Args:
        key (str): redis key
        object_dict (Union[dict, str]): object to be saved
        redis_conn: connection with redis
        time_to_live: TTL of the key, so it can be erased automatically

    Returns:
        returns a boolean with the status of the operation

    """
    if isinstance(object_to_save, dict) or isinstance(object_to_save, list):
        # object_to_save = simplejson.dumps(object_to_save, default=parser.json_serializer)
        object_to_save = pickle.dumps(object_to_save)

    ret = await redis_conn.set(name=key, value=object_to_save, keepttl=time_to_live)
    await redis_conn.expire(key, time_to_live)
    return ret


async def read_dict_from_redis_async(key: str, redis_conn: Redis) -> Union[str, dict]:
    """Read dictionary from redis, they are being stored as string so this methods does the conversion to dict

    Args:
        key (str): redis key
        redis_conn (redis.Redis): connection with redis

    Returns:
        returns a dictionary or a string, if some error occur returns a empty dict

    """
    result = {}
    try:
        ret = await redis_conn.get(key)
        if ret:
            # result = simplejson.loads(ret)
            result = pickle.loads(ret)
    except simplejson.JSONDecodeError:
        return result
    except:
        logger.log_message(f"Error tring to get value from redis {traceback.print_exc()}", level=logging.ERROR)
        result = {}
    return result


async def get_object_from_redis_async(redis_connection_info: RedisConnectionInfo, redis_key: str, close_connection: bool = True) -> dict:
    """Method to make easier the process of getting information from redis
    Args:
        redis_connection_info (RedisConnectionInfo): connection info
        redis_key (str): key to be retrieved
    Returns:
        returns a dict with the value stored on redis

    Example:
        conn_info = redis.RedisConnectionInfo(
            settings.credentials['redis']['hostname'],
            settings.credentials['redis'].getint('port'),
            settings.credentials['redis']['password'],
        )
        result = await redis.get_object_from_redis_async(conn_info, identifier)
        if result:
            return result
    """
    redis_conn = None
    result = {}
    logger.log_message(f'requesting object from redis: {redis_key}')
    try:
        redis_conn = await get_redis_connection_async(redis_connection_info)
        if not redis_conn:
            logger.log_message("No connection received from method get_redis_connection", level=logging.WARNING)
            return result

        result = await read_dict_from_redis_async(key=redis_key, redis_conn=redis_conn)
    except:
        logger.log_message(f"Error tring to retrieve object from redis {traceback.print_exc()}", level=logging.ERROR)
    finally:
        if redis_conn and close_connection:
            await redis_conn.close()

    logger.log_message(f'retrieving object from redis: {redis_key}')
    return result


async def set_object_on_redis_async(
        redis_connection_info: RedisConnectionInfo, redis_key: str,
        object_to_save: Union[str, dict], time_to_live: int = 300) -> bool:
    redis_conn = None
    result = False
    try:
        redis_conn = await get_redis_connection_async(redis_connection_info)
        if not redis_conn:
            logger.log_message("No connection received from method get_redis_connection", level=logging.WARNING)
            return result

        result = await write_object_into_redis_async(key=redis_key, object_to_save=object_to_save, redis_conn=redis_conn, time_to_live=time_to_live)
    except:
        logger.log_message(f"Error tring to retrieve object from redis {traceback.print_exc()}", level=logging.ERROR)
    finally:
        if redis_conn:
            await redis_conn.close()

    return result


async def main_async():
    credentials = parser.read_ini_file(settings.credentials_file_path)
    if not credentials:
        return

    conn_info = RedisConnectionInfo(
        credentials['redis']['hostname'],
        credentials['redis'].getint('port'),
        credentials['redis']['password'],
    )
    # redis_conn = await get_redis_connection_async(conn_info)
    await asyncio.gather(*[
        set_object_on_redis_async(conn_info, f"teste_{i}", {f"teste_{i}": i})
        for i in range(1)
    ])
    object_r = await asyncio.gather(*[
        get_object_from_redis_async(conn_info, f"teste_{i}")
        for i in range(1)
    ])
    return object_r
