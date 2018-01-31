#!/usr/bin/env sh

exec /usr/bin/uwsgi --ini /app/uwsgi.ini --need-app
