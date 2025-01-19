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

case "$2" in
    openai)
        EXPORT_ENV_VAR="OPENAI_API_KEY"
        echo "Injecting OPENAI_API_KEY into the container."
        ;;
    google)
        EXPORT_ENV_VAR="GOOGLE_API_KEY"
        echo "Injecting GOOGLE_API_KEY into the container."
        ;;
    gemini)
        EXPORT_ENV_VAR="GEMINI_API_KEY"
        echo "Injecting GEMINI_API_KEY into the container."
        ;;
    *)
        EXPORT_ENV_VAR=""
        echo "Running container without LLM post-processing. To change, rerun this script with one of [openai, google, gemini] which injects the corresponding API key into the container."
        exit 1
        ;;
esac

# Run the Docker container
# docker run --rm -it -p 8000:8000 $DOCKER_ARGS $VOLUME_MOUNT $IMAGE_NAME /bin/bash -c "echo 'source /home/mineru/mineru_venv/bin/activate' >> ~/.bashrc && exec bash"
docker run --rm -it -p 8000:8000 -e $EXPORT_ENV_VAR $DOCKER_ARGS $VOLUME_MOUNT $IMAGE_NAME /bin/bash -c "echo 'source /home/mineru/mineru_venv/bin/activate' >> ~/.bashrc && exec bash"
