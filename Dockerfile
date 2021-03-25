FROM python:3.7.10-slim as base
LABEL MAINTAINER="dcueng@godaddy.com"

RUN addgroup dcu && adduser --disabled-password --disabled-login --no-create-home --ingroup dcu --system dcu
RUN apt-get update && apt-get install -y gcc

RUN pip install -U pip
COPY ./private_pips /tmp/private_pips
RUN pip install --compile /tmp/private_pips/dcdatabase
RUN pip install --compile /tmp/private_pips/PyAuth

FROM base as deliverable

# Move files to new dir
RUN mkdir -p /app
COPY ./*.ini ./*.py ./logging.yaml /app/

# Compile the Flask API
RUN mkdir /tmp/build
COPY . /tmp/build
RUN pip install --compile /tmp/build

# Expose Flask port 5000
EXPOSE 5000

# cleanup
RUN apt-get remove --purge -y gcc
RUN rm -rf /tmp

# Fix permissions.
RUN chown -R dcu:dcu /app

WORKDIR /app

ENTRYPOINT ["/usr/local/bin/uwsgi", "--ini", "/app/uwsgi.ini", "--need-app"]
