DIR=$pwd

docker rm -f magic_formula_redis
docker run --name magic_formula_redis -p 6379:6379 -d -v $DIR/src/config/redis.conf:/etc/redis/redis.conf:ro --restart always redis:latest

