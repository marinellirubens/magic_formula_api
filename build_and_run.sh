#!/bin/bash
sh build_image.sh
sh start_redis_container.sh
sh start_service_container.sh
sh start_api_container.sh
