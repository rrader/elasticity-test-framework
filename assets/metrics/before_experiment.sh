#!/usr/bin/env bash

# little magic
service metrics.sh stop
service metrics.sh start
sleep 2
service metrics.sh stop

rm -f /var/log/metrics.sh.log
service metrics.sh start
