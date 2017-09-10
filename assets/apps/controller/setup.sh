#!/usr/bin/env bash
set -x

pip3 install -r requirements.txt
python3 setup.py develop

cp -f /opt/test/assets/apps/controller/init.scaling_controller.sh /etc/init.d/scaling_controller
chmod +x /etc/init.d/scaling_controller
update-rc.d scaling_controller defaults

cp -f /opt/test/assets/apps/controller/init.metrics_collector.sh /etc/init.d/metrics_collector
chmod +x /etc/init.d/metrics_collector
update-rc.d metrics_collector defaults

python3 /opt/test/assets/apps/controller/scaling_controller/init_db.py
