# MinerU Server

MinerU Server is a microservice designed for processing PDFs using the [magic-pdf](https://github.com/opendatalab/MinerU/) library. The service includes enhancements for running efficiently in a Dockerized environment, making it easy to deploy as a microservice.

## Features

- **PDF Processing**: Automatically processes PDFs to markdown using advanced models for layout detection and OCR.
- ~~**Model Management**: Downloads and manages models at runtime, ensuring minimal Docker image size.~~ (changed that for now to have a fully self-contained container)
- **Asynchronous Task Handling**: Handles multiple file processing tasks concurrently.
- **Easy Deployment**: Ready to be deployed as a Docker container, simplifying integration into any microservice architecture.

## Prerequisites

- **Docker**: Ensure Docker is installed on your system.
- **Git LFS**: Git Large File Storage (LFS) is required for managing large model files.

## Installation

### 1. Clone the Repository

```bash
git clone git@github.com:DerEchteFeuerpfeil/mineru-server.git
cd mineru-server
```

### 2. Build the Docker Images

I have provided two separate Dockerfiles, one for deploying the application on a GPU machine and one for active development (also uses GPU for now). Difference is that the one for active development mounts this directory instead of copying. The output and db file during development can be found in the `data` directory that is created during runtime. 

```bash
./build.sh
```

### 3. Run the Docker Container

Run the Docker container, exposing the necessary ports.

```bash
./run.sh dev
```

or 

```bash
./run.sh gpu
```

and inside the container (currently you get a bash instead of the server auto-starting) just do:
```bash
python main.py
```

### 4. Access the API

Once the container is running, you can interact with the service via the API:

- **Upload PDF**: `POST /upload`
- **Download Processed File**: `GET /download/{task_id}`

## Notes
- the magic-pdf call is hardcoded for german and force-ocr, if you wish something different pls edit the `api/v1/services/Pdf2MD.py`
- there is currently no CPU Dockerfile, the user `ulan-yisaev` created `old.Dockerfile` for that but I have not tested it yet

## Contributing

Ima be real with you, I do not intend to maintain this as an open-source project. If you would like to further use this, feel free to clone it. I still appreciate issues if something doesn't work as expected and I'll try to get to them asap.

### Suggested Improvements

- more endpoints for the currently very limited API
- tests
- CPU build
