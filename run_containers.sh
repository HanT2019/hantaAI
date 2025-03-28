#!/bin/sh
rm -rf /var/lib/docker/containers/*
docker run --name speed-detection --rm -dit --gpus all -p 8081:80 -v /tmp:/tmp speed-server
docker run --name 3dbb-detection --rm -dit --gpus all -p 8080:80 -v /tmp:/tmp 3dbb-server
