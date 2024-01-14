import os

from flask import Blueprint, send_file
from flask_swagger_ui import get_swaggerui_blueprint
from flask_cors import CORS


swagger_base_bp = Blueprint('swagger_base', __name__)
CORS(swagger_base_bp, resource={r"/*": {"origins": "*"}})
swagger_path = './docs/swagger.yaml'

SWAGGER_URL = '/docs'
API_URL = '/swagger'


@swagger_base_bp.after_request
def add_response_headers(response):
    response.headers['Cache-Control']= 'no-cache,no-store,must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'

    if 'HOSTNAME' in os.environ:
        response.headers['X-Serving-Host'] = os.environ['HOSTNAME']
    return response


@swagger_base_bp.route(API_URL)
def swagger_json():
    return send_file(swagger_path)


@swagger_base_bp.route(API_URL + '2')
def swagger_json2():
    return {}


swagger_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,  # Swagger UI static files will be mapped to '{SWAGGER_URL}/dist/'
    API_URL,
    config={  # Swagger UI config overrides
        'spec': "Test application"
    },
)
