# Build pytket-quest from source code
FROM python:3.10-slim

RUN apt-get update && \
    apt-get clean && apt-get purge && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

WORKDIR /app/

COPY ./pytket ./pytket/
COPY ./setup.py .
COPY ./_metadata.py .
COPY ./README.md .

RUN python3 setup.py bdist_wheel
