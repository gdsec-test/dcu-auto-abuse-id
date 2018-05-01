# AUTO_ABUSE_ID
#
#

FROM ubuntu:16.04
MAINTAINER DCU ENG <DCUEng@godaddy.com>

RUN groupadd -r dcu && useradd -r -m -g dcu dcu

# apt-get installs
RUN apt-get update && \
    apt-get install -y build-essential \
    fontconfig \
    gcc \
    libffi-dev \
    libssl-dev \
    python-dev \
    python-pip \
    curl

COPY ./*.ini ./*.sh ./run.py ./celeryconfig.py ./encryption_helper.py ./settings.py ./*.yml /app/

COPY . /tmp

# pip install private pips staged by Makefile
RUN for entry in PyAuth blindAl dcdatabase; \
    do \
    pip install --compile "/tmp/private_pips/$entry"; \
    done

RUN pip install --compile /tmp

# cleanup
RUN apt-get remove --purge -y build-essential \
    gcc \
    libffi-dev \
    libssl-dev \
    python-dev && \
    rm -rf /var/lib/apt/lists/* && \
    rm -rf /tmp && \
    chown -R dcu:dcu /app

# Expose Flask port 5000
EXPOSE 5000
USER dcu
WORKDIR /app

ENTRYPOINT ["/app/runserver.sh"]
