import json
import sqlite3
import time

import paramiko

from scaling_controller.consts import DB_PATH, GET_LAST_METRIC, KEY, MAX_INSTANCES

METRICS = ['cpu']


class Env:
    def __init__(self):
        self.started = time.time()
        self.vars = {}
        self.instances = 0
        self.max_instances = MAX_INSTANCES
        self.con = sqlite3.connect(DB_PATH)

    def time(self):
        return time.time() - self.started

    def last_metrics(self):
        cur = self.con.cursor()
        metrics = []
        for i in range(self.instances):
            metrics.append({})
            instance = '{}.target'.format(i)
            for metric in METRICS:
                cur.execute(GET_LAST_METRIC, [instance, metric])
                value = cur.fetchone()
                if value is not None:
                    value, = value
                metrics[i][metric] = value
        cur.close()
        print(json.dumps(metrics))
        return metrics

    def set_instance_number(self, n):
        print('Set instance number to {}...'.format(n))

        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(hostname='0.loadbalancer', username='root', key_filename=KEY, port=22)
        stdin, stdout, stderr = client.exec_command('bash /opt/test/assets/haproxy/haproxy_control.sh {}'.format(n))
        data = stdout.read() + stderr.read()
        print(data)
        client.close()

        self.instances = n
