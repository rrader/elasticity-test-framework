import os
import socket
import time

import sys
from queue import Queue, Empty
from threading import Thread

import requests
from pygtail import Pygtail
from requests import Timeout, HTTPError

METRICS_SH = '/var/log/metrics.sh.log'
HOSTNAME = socket.gethostname()
METRICS_COLLECTOR_URL = 'http://0.controller/put/{}'.format(HOSTNAME)

METRICS_QUEUE = Queue()


def put_metrics():
    while True:
        try:
            value = METRICS_QUEUE.get(timeout=2)
        except Empty:
            print('queue is empty...')
            continue
        url = '{}/{}'.format(METRICS_COLLECTOR_URL, value['metric'])
        print('put to', url)
        try:
            response = requests.put(
                url,
                json={
                    'timestamp': value['timestamp'],
                    'value': value['value'],
                },
                timeout=2
            )
            print(response.status_code)
            response.raise_for_status()
        except Timeout:
            print('timed out')
            METRICS_QUEUE.put(value)
            time.sleep(5)
        except HTTPError as e:
            print('error!', str(e))
            METRICS_QUEUE.put(value)
            time.sleep(5)
        except Exception as e:
            print('unknown error', str(e))
            METRICS_QUEUE.put(value)
            time.sleep(5)


def main():
    Thread(target=put_metrics).start()

    while not os.path.exists(METRICS_SH):
        print('Waiting for {}...'.format(METRICS_SH))
        time.sleep(1)

    while True:
        for line in Pygtail(METRICS_SH):
            try:
                metric, value = line.split(': ')
                value = float(value.strip())
                if ' ' in metric:
                    raise ValueError

            except ValueError:
                print('invalid line', line.strip())
                continue

            METRICS_QUEUE.put(
                {
                    'timestamp': time.time(),
                    'value': value,
                    'metric': metric,
                }
            )
            print('queued', line.strip())
        time.sleep(5)
        print('no new data...')


if __name__ == '__main__':
    main()
