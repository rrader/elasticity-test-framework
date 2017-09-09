import os
import time

import sys
from pygtail import Pygtail

METRICS_SH = '/var/log/metrics.sh.log'


def main():
    while not os.path.exists(METRICS_SH):
        print('Waiting for {}...'.format(METRICS_SH))
        time.sleep(1)

    while True:
        for line in Pygtail(METRICS_SH):
            sys.stdout.write(line)
        time.sleep(1)


if __name__ == '__main__':
    main()
