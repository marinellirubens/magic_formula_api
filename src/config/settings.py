"""File to hold global variables and configurations that will change depending on the server, and/or environment"""
import threading


file_ttl_minutes = 50
time_to_sleep_minutes = 60
parallel_number_requests = 6
use_cache = False

request_uniques = threading.local()
"""variable to handle information that should not be shared between threads"""

socket_client_handler = {
    "host": "localhost",
    "port": 9020
}
"""Configuration on the socket for logging"""

credentials_file_path = 'config/credentials.ini'
"""file for the credentials file"""

credentials = {}
"""place holder for the credentials that will be imported from credentials.ini file"""

UNAUTHORIZED_RESPONSE = ("no Authorization header/session cookie found", 401)
"""Default response when sending a 401/Unauthorized response"""

SWAGGER_FILE_PATH = 'docs/swagger.yaml'
NOT_FOUND_DB_RESPONSE = ("No information retrieved from the database", 405)
"""Default response when sending a 401/Unauthorized response"""
