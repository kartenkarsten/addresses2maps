# Use an official Python runtime as a parent image
FROM python:2.7-slim@sha256:6c1ffdff499e29ea663e6e67c9b6b9a3b401d554d2c9f061f9a45344e3992363

# Set the working directory to /data
WORKDIR /data

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install --trusted-host pypi.python.org pysvg geocoder

# Install wget
RUN apt-get -o Debug::pkgProblemResolver=true -o Debug::Acquire::http=true update && apt-get install -y wget && rm -rf /var/lib/apt/lists/*
# Install wget
#RUN apt-get update && apt-get install -y wget gnupg && \
#    apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys 0x87F5DA04EC26272C && \
#    apt-get update

# Run the command to start the application
ENTRYPOINT ["python", "/app/vcard2maps.py"]
