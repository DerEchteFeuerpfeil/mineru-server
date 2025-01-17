#!/bin/bash

# Check if an argument is passed
if [ "$#" -lt 1 ]; then
    echo "Usage: $0 [gpu|cpu|dev]"
    exit 1
fi

# Determine the Dockerfile based on the argument
case "$1" in
    gpu)
        IMAGE_NAME="mineru-gpu:latest"
        DOCKER_ARGS="--gpus=all"
        VOLUME_MOUNT=""
        ;;
    cpu)
        IMAGE_NAME="mineru-cpu:latest"
        DOCKER_ARGS=""
        VOLUME_MOUNT=""
        ;;
    dev)
        IMAGE_NAME="mineru-dev:latest"
        DOCKER_ARGS="--gpus=all"
        VOLUME_MOUNT="-v $(pwd):/home/mineru/app"
        ;;
    *)
        echo "Invalid argument. Use one of: gpu, cpu, dev"
        exit 1
        ;;
esac

# Run the Docker container
docker run --rm -it -p 8000:8000 $DOCKER_ARGS $VOLUME_MOUNT $IMAGE_NAME /bin/bash -c "echo 'source /home/mineru/mineru_venv/bin/activate' >> ~/.bashrc && exec bash"
