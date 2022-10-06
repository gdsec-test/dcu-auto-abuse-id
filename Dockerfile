FROM docker-dcu-local.artifactory.secureserver.net/dcu-python3.7:3.3
LABEL MAINTAINER="dcueng@godaddy.com"

USER root

RUN apt-get update && apt-get install -y gcc

RUN pip install -U pip

# Compile the Flask API
RUN mkdir -p /tmp/build
COPY requirements.txt /tmp/build/
COPY pip_config /tmp/build/pip_config
RUN PIP_CONFIG_FILE=/tmp/build/pip_config/pip.conf pip install -r /tmp/build/requirements.txt

COPY . /tmp/build
RUN PIP_CONFIG_FILE=/tmp/build/pip_config/pip.conf pip install --compile /tmp/build

# Expose Flask port 5000
EXPOSE 5000

# Move files to new dir
RUN mkdir -p /app
COPY ./*.ini ./*.py /app/
# cleanup
RUN apt-get remove --purge -y gcc
RUN rm -rf /tmp
# Fix permissions.
RUN chown -R dcu:dcu /app
WORKDIR /app

USER dcu
ENTRYPOINT ["/usr/local/bin/uwsgi", "--ini", "/app/uwsgi.ini", "--need-app"]
