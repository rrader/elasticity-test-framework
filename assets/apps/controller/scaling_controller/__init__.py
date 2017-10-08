import sys

from scaling_controller.algs.constant import constant
from scaling_controller.algs.cpu_threshold import cpu_threshold
from scaling_controller.algs.time_based import time_based
from scaling_controller.utils import Env


ALGORITHM = cpu_threshold


def main():
    print('started')
    env = Env()

    env.set_instance_number(1)
    for alg_out in ALGORITHM(env):
        print(alg_out)
        sys.stdout.flush()


if __name__ == '__main__':
    main()
