from time import sleep

from elasticity_analyzer.extensions.httperf import plot_httperf
from elasticity_analyzer.extensions.metrics import collect_metrics
from elasticity_analyzer.setups.base import BaseExperiment


class BlogBalancer(BaseExperiment):
    """
    Experiment starts multiple machines with load balancer,
    runs the load test,
    and measures the metrics for 30 seconds
    """
    DEFAULT_ASSETS = ['general', 'hosts', 'metrics']
    LAYOUT = {
        'groups': {
            'Target': {
                'number': 3,
                'assets': ['metrics/agent', 'apps/blog', 'apps/blog-nginx'],
                'size': '512mb'
            },
            'LoadBalancer': {
                'number': 1,
                'assets': ['haproxy'],
                'size': '512mb'
            },
            'Controller': {
                'number': 1,
                'assets': ['apps/controller'],
                'size': '512mb'
            },
            'Source': {
                'number': 1,
                'assets': ['apps/httperf'],
                'size': '512mb'
            },
        }
    }

    TIMEOUT = 1  # seconds
    START_RATE = 5
    MAX_RATE = 50
    STEP_DURATION = 15
    STEP_RATE = 10
    PORT = 80

    def __init__(self):
        super().__init__()
        self.httperf_files = []

    def experiment(self):
        sleep(10)

        timeout = self.TIMEOUT

        with self.ssh_droplet_group('Source') as sshs:
            max_rate = self.MAX_RATE
            rate = self.START_RATE
            dur = self.STEP_DURATION
            port = self.PORT

            while rate < max_rate:
                conns = rate * dur
                cmd = (
                    f'httperf --hog --server=0.loadbalancer --port {port} --num-conns {conns} --rate={rate} '
                    f'--timeout={timeout} > /tmp/httperf-{rate}.log'
                )
                self.httperf_files.append((f'/tmp/httperf-{rate}.log', f'httperf-{rate}.log'))
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
        sleep(30)

    def before_experiment(self):
        super().before_experiment()

    def after_experiment(self):
        super().after_experiment()

    def collect(self):
        super().collect()
        collect_metrics(self)

        print('=> Download httperf log files')
        log_files = []
        for droplet in self.get_droplet_group('Source'):
            with self.ssh_droplet(droplet) as ssh:
                output = self.output_dir(f'Source/{droplet.name}')
                sftp = ssh.open_sftp()
                for remote_file, name in self.httperf_files:
                    sftp.get(remote_file, f'{output}/{name}')
                    log_files.append(f'{output}/{name}')

            plot_httperf(self, log_files, output)

    def setup(self):
        super().setup()

    # def run(self):  # comment out for full experiment run
    #     self.before_experiment()
    #     self.experiment()
    #     self.after_experiment()
    #
    #     self.collect()


if __name__ == "__main__":
    BlogBalancer().run()
