#!/usr/bin/env bash
set -x

service gunicorn stop
service gunicorn start
