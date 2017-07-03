#!/usr/bin/env bash
set -x

apt-get update --fix-missing
apt-get install -y python3 python3-pip
pip3 install -r requirements.txt

cp -f /opt/test/assets/apps/blog/init.gunicorn.sh /etc/init.d/gunicorn
chmod +x /etc/init.d/gunicorn
update-rc.d gunicorn defaults
