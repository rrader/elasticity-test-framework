#!/usr/bin/env bash
set -x

pip3 install -r requirements.txt

cp -f /opt/test/assets/apps/blog/init.gunicorn.sh /etc/init.d/gunicorn
chmod +x /etc/init.d/gunicorn
update-rc.d gunicorn defaults
