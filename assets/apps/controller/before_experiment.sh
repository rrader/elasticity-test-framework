#!/usr/bin/env bash

service scaling_controller stop
service metrics_collector stop

python3 /opt/test/assets/apps/controller/scaling_controller/init_db.py

service scaling_controller start
service metrics_collector start
