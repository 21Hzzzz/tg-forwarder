# Install Docker
https://docs.docker.com/engine/install/ubuntu/#install-using-the-repository

# Setup Project
git clone https://github.com/21Hzzzz/tg-forwarder.git

cd tg-forwarder

cp .env.example .env

nano .env

# Build Image
docker build -t tg-forwarder:latest .

# First Login (interactive, enter Telegram code)
docker run --rm -it --name tg-forwarder-login --env-file .env -v "${PWD}/sessions:/app/sessions" -v "${PWD}/chat_filters.json:/app/chat_filters.json" tg-forwarder:latest

# Run in Background
docker run -d --name tg-forwarder-app-1 --restart unless-stopped --env-file .env -v "${PWD}/sessions:/app/sessions" -v "${PWD}/chat_filters.json:/app/chat_filters.json" tg-forwarder:latest

# View Logs
docker logs -f -t tg-forwarder-app-1

# Stop and Remove
docker stop tg-forwarder-app-1
docker rm tg-forwarder-app-1

# Update
cd tg-forwarder
git pull
nano .env
docker build -t tg-forwarder:latest .
docker rm -f tg-forwarder-app-1
docker run -d --name tg-forwarder-app-1 --restart unless-stopped --env-file .env -v "${PWD}/sessions:/app/sessions" -v "${PWD}/chat_filters.json:/app/chat_filters.json" tg-forwarder:latest

## Required Environment Variables

- `TG_API_ID`
- `TG_API_HASH`
- `TG_PHONE` (required, not optional)
- `FILTER_CONFIG_PATH` (points to JSON containing chat filters)
- `PUSHPLUS_TOKEN`
