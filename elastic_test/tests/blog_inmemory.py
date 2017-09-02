from time import sleep

from elastic_test.setups.base import BaseExperiment
from elastic_test.setups.metrics import MetricsSetup


class BlogInMemory(MetricsSetup, BaseExperiment):
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

    def __init__(self):
        super().__init__()
        self.files = []

    def experiment(self):
        target = self.get_droplet_group('Target')[0].ip_address

        with self.ssh_droplet_group('Source') as sshs:
            max_rate = 500
            rate = 200
            dur = 15

            while rate < max_rate:
                conns = rate * dur
                cmd = (
                    f'httperf --hog --server={target} --port 5000 --num-conns {conns} --rate={rate} --timeout=1 '
                    f'> /tmp/httperf-{rate}.log'
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

                rate = int(rate + 10)

    def before_experiment(self):
        super().before_experiment()

    def after_experiment(self):
        super().after_experiment()

    def collect(self):
        super().collect()
        for droplet in self.get_droplet_group('Source'):
            with self.ssh_droplet(droplet) as ssh:
                output = self.output_dir(f'Source/{droplet.name}')
                sftp = ssh.open_sftp()
                for remote_file, name in self.files:
                    sftp.get(remote_file, f'{output}/{name}')

    def setup(self):
        super().setup()


if __name__ == "__main__":
    BlogInMemory().run()
