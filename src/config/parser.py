from datetime import datetime, date
from typing import Union
from uuid import UUID
import configparser
import json
import os


def read_json_file(file_path: str) -> dict:
    """Reads json file and returns a dictionary with the information

    Args:
        file_path (str): path of the json file

    Returns:
        dictionary with the file, if file does not exists return a empty dict
    """
    file_info = {}
    if not os.path.exists(file_path):
        return file_info

    with open(file_path) as file:
        file_info = json.load(file)
    return file_info


def read_ini_file(file_path: str) -> Union[configparser.ConfigParser, None]:
    """Method to read config file on ini format and return a parser for this configuration

    Args:
        file_path (str): path of the ini file

    Returns:
        a parser for the configuration on the file, if file does not exists returns None
    """
    if not os.path.exists(file_path):
        return None

    parser = configparser.ConfigParser()
    parser.read(file_path)
    return parser


def json_serializer(obj):
    """Function to convert the datetime objects where there is a serialization of a json containing a date or datetime"""
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if isinstance(obj, (UUID)):
        return str(obj)
    raise TypeError(f'Type {type(obj)} is not serializable')

