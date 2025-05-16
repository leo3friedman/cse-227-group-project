FROM node:23-slim

# Install basic tools including Python
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        git \
        ca-certificates \
        unzip \
        diffoscope \
        python3 \
        python3-pip \
        python3-venv && \
    ln -s /usr/bin/python3 /usr/bin/python && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Create and activate a virtual environment
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python packages
COPY requirements.txt /workspace/
RUN pip install -r /workspace/requirements.txt

WORKDIR /workspace

CMD ["bash"]
