#!/bin/sh
cd hantaAI-3dbb-detection-docker
git pull
cd ../hantaAI-opponent-speed-docker
git pull

docker stop speed-detection
docker container prune -f
docker rmi speed-server
docker build -t speed-server .
docker run --name speed-detection --restart=always -dit --gpus all -p 8081:80 -v /tmp:/tmp speed-server

cd ../hantaAI-3dbb-detection-docker

docker stop 3dbb-detection
docker container prune -f
docker rmi 3dbb-server
docker build -t 3dbb-server .
docker run --name 3dbb-detection --restart=always -dit --gpus all -p 8080:80 -v /tmp:/tmp 3dbb-server
