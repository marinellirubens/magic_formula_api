#!/bin/bash
CWD=$(pwd)
gunicorn --name=magic_formula --workers=3 --threads=15  --worker-class=gthread \
    --max-requests 1000 --timeout 60 --bind 0.0.0.0:8090 "api:main()"
