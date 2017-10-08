from statistics import mean
from time import sleep

from scaling_controller.utils import MovingAverage

COOLDOWN_SECONDS = 30
CPU_THRESHOLD = 90


def cpu_threshold(env):
    cpu_avg = MovingAverage(window_size=10)
    last_scaled = None
    while True:
        # gather metrics
        cpu = get_target_cpu_avg(env)
        if cpu is None:
            yield 'No data yet'
        cpu_avg.put(cpu)

        # Cool down
        if last_scaled is not None:
            if env.time() - last_scaled < COOLDOWN_SECONDS:
                yield 'waiting for 30 sec'

        # Scale if needed
        if cpu_avg.get():
            print('avg 10s window:', cpu_avg.get())

            if cpu_avg.get() >= CPU_THRESHOLD:

                if env.instances + 1 > env.max_instances:
                    yield 'Overload! Maximum instance number exceeded!'

                env.set_instance_number(env.instances + 1)
                last_scaled = env.time()

        sleep(1)


def get_target_cpu_avg(env):
    cpu = [instance['cpu'] for instance in env.last_metrics('target')]
    if cpu and None not in cpu:
        return mean(cpu)
