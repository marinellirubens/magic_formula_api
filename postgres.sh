#!/bin/bash
CONTAINER_PORT=5432
CONTAINER_NAME=postgres_mf
docker rm -f $CONTAINER_NAME

# a file with the password called postgres_pass must be on the same directory
PASSWORD=`cat postgres_pass`

if [ $(docker volume ls --format={{.Name}} | grep "postgres_data_mf") = "postgres_data_mf" ]
then
    echo Skipping volume creation, volume already exists
else
    echo Creating volume postgres_data_mf
    docker volume create postgres_data_mf
fi

docker run --name $CONTAINER_NAME \
    -e POSTGRES_PASSWORD=$PASSWORD \
    -e POSTGRES_USER=MFDB \
    -e POSTGRES_DB=magic_formula \
    -v postgres_data:/var/lib/postgresql/data \
    -p $CONTAINER_PORT:5432 \
    -d postgres:15

