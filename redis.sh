docker rm -f redis_mf 
docker run --name redis_mf -p 6379:6379 -d -v ./redis.conf:/etc/redis/redis.conf:ro --restart always redis:latest

