# Stage 1: Build Detectron2 from source
FROM nvidia/cuda:11.7.1-cudnn8-devel-ubuntu22.04 as detectron2-build

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.10 \
    python3.10-venv \
    python3.10-distutils \
    python3-pip \
    python3-opencv \
    ca-certificates \
    python3-dev \
    cmake \
    ninja-build \
    wget \
    git \
    git-lfs \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.10 1 && \
    ln -sv /usr/bin/python3 /usr/bin/python && \
    git lfs install && \
    python3 -m venv /opt/mineru_venv

ENV VIRTUAL_ENV=/opt/mineru_venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

RUN pip install --no-cache-dir pip-tools && \
    pip install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu117

RUN git clone --depth 1 https://github.com/facebookresearch/detectron2.git /opt/detectron2_repo && \
    cd /opt/detectron2_repo && \
    sed -i 's|"omegaconf>=2.1,<2.4"|"omegaconf>=2.4.0.dev2"|g' setup.py && \
    python setup.py bdist_wheel && \
    rm -rf /opt/detectron2_repo/.git /opt/detectron2_repo/build

# Stage 2: Final image with the built Detectron2 wheel and other dependencies
FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.10 \
    python3.10-venv \
    python3.10-distutils \
    python3-pip \
    python3-opencv \
    ca-certificates \
    git \
    git-lfs \
    libgl1 \
    libglib2.0-0 \
    wget \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.10 1 && \
    ln -sv /usr/bin/python3 /usr/bin/python && \
    python3 -m venv /opt/mineru_venv

ENV VIRTUAL_ENV=/opt/mineru_venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Copy the built Detectron2 wheel from the first stage
COPY --from=detectron2-build /opt/detectron2_repo/dist/*.whl /wheels/

# Install the Detectron2 wheel and other Python dependencies
RUN pip install --no-cache-dir /wheels/*.whl && rm -rf /wheels

# The models are now downloaded at runtime to avoid large image size
#RUN git lfs install && \
#    git lfs clone https://huggingface.co/wanderkid/PDF-Extract-Kit /opt/models/PDF-Extract-Kit && \
#    mv /opt/models/PDF-Extract-Kit/models/* /opt/models/ && \
#    rm -rf /opt/models/PDF-Extract-Kit/.git /opt/models/PDF-Extract-Kit/* /opt/models/PDF-Extract-Kit/.git-lfs && \
#    test -f /opt/models/MFD/weights.pt && \
#    test -f /opt/models/Layout/config.json && \
#    test -f /opt/models/MFR/UniMERNet/config.json && \
#    test -f /opt/models/TabRec/StructEqTable/config.json \
#    || (echo "Model files are missing after moving" && exit 1)

COPY magic-pdf.json /root/magic-pdf.json
RUN sed -i 's|/tmp/models|/opt/models|g' /root/magic-pdf.json

COPY requirements.txt /app/requirements.txt

RUN pip install --upgrade pip && \
    pip install --no-cache-dir 'magic-pdf[full-cpu] @ git+https://github.com/opendatalab/MinerU' && \
    pip install --no-cache-dir -r /app/requirements.txt && \
    rm -rf /root/.cache /tmp/* /var/tmp/*

COPY . /app
WORKDIR /app

EXPOSE 8000

CMD ["/bin/bash", "-c", "source /opt/mineru_venv/bin/activate && uvicorn main:app --host 0.0.0.0 --port 8000 --reload"]
