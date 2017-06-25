#!/usr/bin/env bash
set -x

apt-get install -y git

mkdir -p /opt; cd /opt
[ -d metrics.sh ] || git clone https://github.com/pstadler/metrics.sh.git
cd metrics.sh
# Install the service
ln -sf $PWD/init.d/metrics.sh /etc/init.d/metrics.sh
mkdir -p /etc/metrics.sh && chmod 600 /etc/metrics.sh
cp -f /opt/test/assets/metrics/metrics.ini /etc/metrics.sh/metrics.ini

update-rc.d metrics.sh defaults

