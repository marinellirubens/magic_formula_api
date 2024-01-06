from logging.handlers import SocketHandler
from typing import Union
import inspect
import logging
import os
import subprocess

from flask import current_app as app

from config import settings


def get_module_info() -> tuple:
    """Gets the module information for logging purposes

    Returns:
        func_name, lineno, mod_name
    """
    frm = inspect.stack()[2]
    func_name = frm.function
    lineno = frm.lineno

    mod_name = frm.filename.split('/')[-1].replace('.py', '')
    return func_name, lineno, mod_name


class ModuleInfo:
    def __init__(self, func_name: str, lineno: int, mod_name: str) -> None:
        self.func_name = func_name
        self.lineno = lineno
        self.mod_name = mod_name


# TODO: create tests for this method log_message
def log_message(message, logger=None, level=logging.DEBUG,
                module_info: Union[ModuleInfo, None] = None, api_name: str = ''):
    """Method to abstract logging messages

    Example:
        >>> log_message(f'requesting information from database', logging.DEBUG)

    Args:
        message(str): message that should be logged
        level(int): Logging level, done like this so the function can be dinamic

    Returns:
        None
    """
    session_info = ''
    # use inspect to get which function is calling this function
    if not logger:
        if app:
            logger = app.logger
        elif api_name:
            logger = logging.getLogger(api_name)
        else:
            logging.log(level, message)
            return

    # if the level is below the seted level there is not need to try to log.
    if level < logger.level:
        return

    if not module_info:
        func_name, lineno, mod_name = get_module_info()
    else:
        mod_name = module_info.mod_name
        lineno = module_info.lineno
        func_name = module_info.func_name

    session_info = format_session_info()
    logger.log(level, f"{session_info}[{mod_name}.{func_name}:{lineno}] {message}")


def format_session_info() -> str:
    """Method to format the session info for the logger variable"""
    if not hasattr(settings.request_uniques, 'value'):
        return ''

    session = settings.request_uniques.value
    session_info = f"[requestid: {session['requestid']}]" + \
                   f"[{session['endpoint']}]"

    return session_info


def check_socket_server(api_name: str):
    """Starting the process for logging socket

    Args:
        api (str): api name

    """

    permision_command = f'chmod +x {os.getcwd()}/config/start_logging_socket.sh'
    execute_command = f'{os.getcwd()}/config/start_logging_socket.sh {api_name}'
    process = subprocess.Popen(permision_command, shell=True, stdout=subprocess.PIPE)
    process.wait()

    process = subprocess.Popen(execute_command, shell=True, stdout=subprocess.PIPE)
    process.wait()


# TODO: create tests for this method setup_custom_logger
def setup_custom_logger(api: str, socket_hostname: str, socket_port: int,
                        stream_handler: bool = False, log_level: int = logging.ERROR, logger = None):
    """Does the setup of the logger for the apis

    Args:
        api (str): api name
        stream_handler (bool): flag to say if creates a stream handler

        log_level:

    Returns:

    """
    # checks the socket service server
    check_socket_server(api)

    # created the logger
    if not logger:
        logger = logging.getLogger(api)
    formatter = logging.Formatter(
        fmt=f'[%(asctime)s][%(levelname)s]%(message)s'
    )
    # [sessionid: {sessionid}][requestid: {requestid}][accno: {accno}] [{endpoint}]

    log_folder = '/tmp/logs'
    if not os.path.exists(log_folder):
        os.makedirs(log_folder)

    # creates the handler to interact with the socker server
    handler = SocketHandler(
        host=socket_hostname,
        port=socket_port
    )
    handler.setFormatter(formatter)

    logger.handlers.clear()
    logger.addHandler(handler)
    if log_level:
        logger.setLevel(log_level)

    if stream_handler:
        st_handler = logging.StreamHandler()
        st_handler.setFormatter(formatter)
        logger.addHandler(st_handler)
    return logger

