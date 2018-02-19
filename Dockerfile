# AUTO_ABUSE_ID
#
#

FROM ubuntu:16.10
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

RUN cd /usr/local/share && \
    curl -L https://bitbucket.org/ariya/phantomjs/downloads/phantomjs-2.1.1-linux-x86_64.tar.bz2 | tar xj && \
    ln -s /usr/local/share/phantomjs-2.1.1-linux-x86_64/bin/phantomjs /usr/bin/phantomjs

COPY ./*.ini ./*.sh ./run.py ./encryption_helper.py ./settings.py /app/

COPY . /tmp

# pip install private pips staged by Makefile
RUN for entry in blindAl dcdatabase; \
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
