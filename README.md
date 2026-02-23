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

# 临时进入容器
docker attach tg-forwarder-app-1
Ctrl+C会停止容器
正确退出方式
Ctrl + P
Ctrl + Q

## Required environment variables

- `TG_API_ID`
- `TG_API_HASH`
- `TG_PHONE` (required, not optional)
- `TG_CHATS` (comma-separated targets)
- `PUSHPLUS_TOKEN`
