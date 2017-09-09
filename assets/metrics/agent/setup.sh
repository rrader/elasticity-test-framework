#!/usr/bin/env bash
set -x

pip3 install -r requirements.txt
python3 setup.py develop

cp -f /opt/test/assets/metrics/agent/init.metricsagent.sh /etc/init.d/metricsagent
chmod +x /etc/init.d/metricsagent
update-rc.d metricsagent defaults
