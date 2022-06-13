FROM docker-dcu-local.artifactory.secureserver.net/dcu-python3.7:3.3
LABEL MAINTAINER="dcueng@godaddy.com"

USER root

RUN apt-get update && apt-get install -y gcc

RUN pip install -U pip

# Move files to new dir
RUN mkdir -p /app
COPY ./*.ini ./*.py /app/

# Compile the Flask API
RUN mkdir /tmp/build
COPY . /tmp/build
RUN PIP_CONFIG_FILE=/tmp/build/pip_config/pip.conf pip install --compile /tmp/build

# Expose Flask port 5000
EXPOSE 5000

# cleanup
RUN apt-get remove --purge -y gcc
RUN rm -rf /tmp

# Fix permissions.
RUN chown -R dcu:dcu /app

WORKDIR /app

USER dcu
ENTRYPOINT ["/usr/local/bin/uwsgi", "--ini", "/app/uwsgi.ini", "--need-app"]
