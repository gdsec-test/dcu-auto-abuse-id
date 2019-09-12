# AUTO_ABUSE_ID
#
#

FROM alpine:3.9
MAINTAINER DCUENG <DCUEng@godaddy.com>

RUN addgroup -S dcu && adduser -H -S -G dcu dcu
# apt-get installs
RUN apk update && \
    apk add --no-cache build-base \
    ca-certificates \
    libffi-dev \
    linux-headers \
    openssl-dev \
    python-dev \
    py-pip

WORKDIR /tmp

# Move files to new dir
ADD . /tmp

# pip install private pips staged by Makefile
RUN for entry in PyAuth dcdatabase; \
    do \
    pip install --compile "/tmp/private_pips/$entry"; \
    done

# install other requirements
RUN pip install --compile /tmp

# Expose Flask port 5000
EXPOSE 5000

# Move files to new dir
RUN mkdir -p /app
COPY ./*.ini ./*.py ./logging.yaml ./runserver.sh /app/
RUN chown -R dcu:dcu /app

# cleanup
RUN rm -rf /tmp

WORKDIR /app

ENTRYPOINT ["/app/runserver.sh"]
