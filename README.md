# 安装docker
https://docs.docker.com/engine/install/ubuntu/#install-using-the-repository

# 配置项目
git clone https://github.com/21Hzzzz/tg-forwarder.git

cd tg-forwarder

mv .env.example .env

nano .env

# 第一次登录
docker compose run --rm --service-ports app

# 之后长期运行
docker compose up -d