FROM node:23-slim

# Install git, unzip, diffoscope, and other basic tools
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        git \
        ca-certificates \
        unzip \
        diffoscope && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

CMD [ "bash" ]