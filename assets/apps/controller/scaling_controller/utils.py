import json
import sqlite3
import time
from statistics import mean

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

    def last_metrics(self, group):
        cur = self.con.cursor()
        metrics = []
        for i in range(self.instances):
            metrics.append({})
            instance = '{}.{}'.format(i, group)
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


class MovingAverage:
    def __init__(self, window_size=10):
        self._vals = []
        self._window_size = window_size

    def get(self):
        if len(self._vals) >= self._window_size:
            return mean(self._vals)

    def put(self, v):
        self._vals.append(v)
        if len(self._vals) > 10:
            del self._vals[0]
