# MinerU Server

MinerU Server is a microservice designed for processing PDFs using the [magic-pdf](https://github.com/opendatalab/MinerU/) library and Facebook AI's `Detectron2`. The service includes enhancements for running efficiently in a Dockerized environment, making it easy to deploy as a microservice.

## Features

- **PDF Processing**: Automatically processes PDFs to markdown using advanced models for layout detection and OCR.
- **Detectron2 Integration**: Leverages Detectron2 for enhanced visual recognition.
- **Model Management**: Downloads and manages models at runtime, ensuring minimal Docker image size.
- **Asynchronous Task Handling**: Handles multiple file processing tasks concurrently.
- **Easy Deployment**: Ready to be deployed as a Docker container, simplifying integration into any microservice architecture.

## Prerequisites

- **Docker**: Ensure Docker is installed on your system.
- **Git LFS**: Git Large File Storage (LFS) is required for managing large model files.

Certainly! Here’s the updated part of the README with the note about using the CPU version of Torch:

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/ulan-yisaev/mineru-server
cd mineru-server
```

### 2. Build the Docker Image

The provided Dockerfile builds the environment with all necessary dependencies, including `Detectron2` and the `magic-pdf` library. 

**Note**: This setup uses the CPU version of Torch.

### Torch Version in `requirements.txt`

```plaintext
--extra-index-url https://download.pytorch.org/whl/cpu
torch==2.3.1+cpu
torchvision==0.18.1+cpu
```

This ensures that the application can run on machines without a GPU, making it more accessible for deployment on a broader range of hardware.
If you need to use the GPU version of Torch, you can update the `requirements.txt` file accordingly.

```bash
docker build -t mineru-api .
```

### 3. Run the Docker Container

Run the Docker container, exposing the necessary ports.

```bash
docker run -p 8000:8000 mineru-api
```

### 4. Access the API

Once the container is running, you can interact with the service via the API:

- **Upload PDF**: `POST /upload`
- **Download Processed File**: `GET /download/{task_id}`

## Enhancements and Features

### 1. Detectron2 Installation

The Dockerfile includes the installation of `Detectron2`, enabling enhanced visual processing. The installation process is optimized for CUDA 11.7, making it compatible with modern GPUs.

### 2. Model Management

Models required by `magic-pdf` are managed at runtime, reducing the Docker image size. The application checks for the existence of models at startup and downloads them if necessary.

### 3. Real-Time Logging

Command outputs are logged in real-time, providing better visibility into what the service is doing at any given moment.

### 4. Improved Error Handling

The application now includes enhanced error handling for both producers and consumers, ensuring more reliable task processing.

## Contributing

If you'd like to contribute to this project, please follow these steps:

1. **Fork the Repository**: Create your fork of the repository by clicking the "Fork" button at the top of this page.

2. **Make Your Changes**: Clone your fork locally, make your changes, and commit them with clear commit messages.

3. **Submit a Pull Request**: Once you're ready, submit a pull request from your fork back to the original repository. Please provide a detailed explanation of the changes you made.

```bash
# Fork the repo
git clone https://github.com/ulan-yisaev/mineru-server
cd mineru-server

# Make your changes and commit them
git add .
git commit -m "Your detailed commit message"

# Push changes to your fork
git push origin main

# Open a pull request on GitHub
```

### Suggested Improvements

- **Enhanced API Features**: Add more endpoints to handle different types of document processing.
