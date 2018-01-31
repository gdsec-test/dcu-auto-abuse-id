#!/usr/bin/env sh

exec /usr/local/bin/uwsgi --ini /app/uwsgi.ini --need-app
