#!/usr/bin/env bash

# TODO: Copy config files
apt-get install -y haproxy

sed -i.bak 's/^ENABLED=0$/ENABLED=1/g' /etc/default/haproxy
mv /etc/haproxy/haproxy.cfg /etc/haproxy/haproxy.cfg.original
cp -f /opt/test/assets/haproxy/haproxy.cfg /etc/haproxy/haproxy.cfg
