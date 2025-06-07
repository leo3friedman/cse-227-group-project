FROM node:23-slim

# Install basic tools including Python and xxd
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        git \
        ca-certificates \
        unzip \
        diffoscope \
        vim-common \
        python3 \
        python3-pip \
        python3-venv && \
    ln -s /usr/bin/python3 /usr/bin/python && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Create and activate a virtual environment
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python packages (including jsbeautifier)
COPY requirements.txt /workspace/
RUN pip install -r /workspace/requirements.txt \
    && pip install jsbeautifier

WORKDIR /workspace

CMD ["bash"]
