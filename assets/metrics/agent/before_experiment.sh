#!/usr/bin/env bash

service metricsagent stop
rm /var/log/metrics.sh.log.offset
rm /var/log/metricsagent.log
service metricsagent start
