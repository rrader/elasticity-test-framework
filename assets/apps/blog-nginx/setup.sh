#!/usr/bin/env bash

apt-get install -y nginx
cp -f /opt/test/assets/apps/blog-nginx/site.conf /etc/nginx/sites-enabled/default
