# Use the latest Ubuntu LTS as the base image
FROM ubuntu:latest@sha256:67211c14fa74f070d27cc59d69a7fa9aeff8e28ea118ef3babc295a0428a6d21

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    inkscape \
    imagemagick \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install pysvg-py3 attributes

# allow conversions to PDF even this might be dangerous
RUN sed -i 's/rights="none" pattern="PDF"/rights="read|write" pattern="PDF"/' /etc/ImageMagick-6/policy.xml

COPY svgs2pdf.py /app/svgs2pdf.py

WORKDIR /data

ENTRYPOINT ["python3", "/app/svgs2pdf.py"]

