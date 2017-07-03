#!/usr/bin/env bash

sleep 10
rm -f /var/log/metrics.sh.log
service metrics.sh start
sleep 5
