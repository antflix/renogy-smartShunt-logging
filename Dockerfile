# Use an official Python runtime as a base image
FROM python:3.10-slim

# Set the working directory
WORKDIR /app

# Update sources and include required repositories
RUN echo "deb http://deb.debian.org/debian bullseye main contrib non-free" > /etc/apt/sources.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
    build-essential \
    systemd \
    systemd-sysv \
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

# Copy all application files into the container
COPY . /app

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Command to run the application
# CMD ["python", "main.py"]

# Copy the entrypoint script
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Set the entrypoint script
ENTRYPOINT ["/entrypoint.sh"]