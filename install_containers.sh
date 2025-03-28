#!/bin/sh
if [ ! -e hantaAI-3dbb-detection-docker ]; then
  git clone https://github.com/dashcamProjects/hantaAI-3dbb-detection-docker.git
fi

if [ ! -e hantaAI-opponent-speed-docker ]; then
  git clone https://github.com/dashcamProjects/hantaAI-opponent-speed-docker.git
fi

cd hantaAI-3dbb-detection-docker
docker build -t 3dbb-server .
docker run --name 3dbb-detection --rm -dit --gpus all -p 8080:80 -v /tmp:/tmp 3dbb-server
# docker run --name 3dbb-detection --restart=always -dit --gpus all -p 8080:80 -v /tmp:/tmp 3dbb-server

cd ..

cd hantaAI-opponent-speed-docker
docker build -t speed-server .
docker run --name speed-detection --rm -dit --gpus all -p 8081:80 -v /tmp:/tmp speed-server
# docker run --name speed-detection --restart=always -dit --gpus all -p 8081:80 -v /tmp:/tmp speed-server
