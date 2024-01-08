#!/bin/bash
CONTAINER_NAME=magic_formula_service
IMAGE_NAME=magic_formula:latest

ENTRYPOINT="/usr/bin/entrypoint_service.sh"


docker rm -f $CONTAINER_NAME
# TODO: include the mapping of the credential file
docker run --entrypoint $ENTRYPOINT -d --restart unless-stopped --link magic_formula_redis:magic_formula_redis --name $CONTAINER_NAME $IMAGE_NAME

