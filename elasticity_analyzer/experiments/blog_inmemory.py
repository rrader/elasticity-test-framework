from time import sleep

from elasticity_analyzer.extensions.httperf import plot_httperf
from elasticity_analyzer.extensions.metrics import collect_metrics
from elasticity_analyzer.setups.base import BaseExperiment


class BlogInMemory(BaseExperiment):
    """
    Experiment starts a single machine with metrics module setup and in-memory blog,
    runs the load test,
    and measures the metrics for 30 seconds
    """
    LAYOUT = {
        'groups': {
            'Target': {
                'number': 1,
                'assets': ['metrics', 'apps/blog'],
                'size': '512mb'
            },
            'Source': {
                'number': 1,
                'assets': ['metrics', 'apps/httperf'],
                'size': '512mb'
            },
        }
    }
    TIMEOUT = 1  # seconds
    START_RATE = 200
    MAX_RATE = 410
    STEP_DURATION = 10
    STEP_RATE = 50
    PORT = 5000

    def __init__(self):
        super().__init__()
        self.files = []

    def experiment(self):
        timeout = self.TIMEOUT

        with self.ssh_droplet_group('Source') as sshs:
            max_rate = self.MAX_RATE
            rate = self.START_RATE
            dur = self.STEP_DURATION
            port = self.PORT

            while rate < max_rate:
                conns = rate * dur
                cmd = (
                    f'httperf --hog --server=0.target --port {port} --num-conns {conns} --rate={rate} '
                    f'--timeout={timeout} > /tmp/httperf-{rate}.log'
                )
                self.files.append((f'/tmp/httperf-{rate}.log', f'httperf-{rate}.log'))
                print(cmd)

                chans = [
                    ssh.get_transport().open_session()
                    for ssh in sshs
                ]
                for chan in chans:
                    chan.exec_command(cmd)

                print(f'Waiting until test on rate {rate} ends...')
                while not all(chan.exit_status_ready() for chan in chans):
                    sleep(1)

                rate = int(rate + self.STEP_RATE)
                sleep(5)

    def before_experiment(self):
        super().before_experiment()

    def after_experiment(self):
        super().after_experiment()

    def collect(self):
        super().collect()
        collect_metrics(self)

        log_files = []
        for droplet in self.get_droplet_group('Source'):
            with self.ssh_droplet(droplet) as ssh:
                output = self.output_dir(f'Source/{droplet.name}')
                sftp = ssh.open_sftp()
                for remote_file, name in self.files:
                    sftp.get(remote_file, f'{output}/{name}')
                    log_files.append(f'{output}/{name}')

            plot_httperf(self, log_files, output)

    def setup(self):
        super().setup()


if __name__ == "__main__":
    BlogInMemory().start()
