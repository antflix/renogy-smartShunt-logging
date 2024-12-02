# Use an official Python runtime as a base image
# FROM python:3.12-slim
FROM arm32v7/python:3.12

ENV PYTHONDONTWRITEBYTECODE 1 
ENV PYTHONUNBUFFERED 1
ENV VIRTUAL_ENV=/venv

# Copy everything
COPY . /app
# Set the working directory
WORKDIR /app
# remove virtual directory
RUN rm -rf ./venv
# Copy the bluetooth setup script
RUN chmod +x /app/setup.sh

# Update sources and include required repositories
RUN echo "deb http://deb.debian.org/debian bullseye main contrib non-free" > /etc/apt/sources.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
    build-essential \
    libdbus-glib-1-dev \
    libgirepository1.0-dev \
    libcairo2-dev \
    libjpeg62-turbo-dev \
    libpango1.0-dev \
    libgif-dev \
    g++ \
    meson \
    ninja-build \
    pkg-config \
    bluez \
    dbus \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Run locally?
# RUN apt-get update && apt-get install -y \
#     build-essential \
#     libdbus-glib-1-dev \
#     libgirepository1.0-dev \
#     libcairo2-dev \
#     libjpeg8-dev \
#     libpango1.0-dev \
#     libgif-dev \
#     g++ \
#     && apt-get clean \
#     && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/
RUN python3 -m pip install -r requirements.txt

# Set PYTHONPATH if your application needs custom module paths
ENV PYTHONPATH=/app

CMD ["/bin/bash", "/app/setup.sh"]
ENTRYPOINT ["python3", "/app/main.py"]