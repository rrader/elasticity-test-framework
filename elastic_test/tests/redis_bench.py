from time import sleep

from elastic_test.setups.base import BaseExperiment
from elastic_test.setups.metrics import MetricsSetup


class RedisBenchmark(MetricsSetup, BaseExperiment):
    LAYOUT = {
        'groups': {
            'Redis': {
                'number': 1,
                'assets': ['metrics', 'redis']
            },
        }
    }

    def experiment(self):
        print('experiment started')
        for droplet in self.get_droplet_group('Redis'):
            with self.ssh_droplet(droplet) as ssh:
                ssh.exec_command('redis-benchmark -q -n 1000 -c 10 -P 5 > /tmp/redis-benchmark.txt')
        print('experiment ended')

    def before_experiment(self):
        super().before_experiment()
        sleep(10)

    def after_experiment(self):
        super().after_experiment()

    def collect(self):
        super().collect()
        for group in self.LAYOUT.get('groups', {}):
            for droplet in self.get_droplet_group(group):
                with self.ssh_droplet(droplet) as ssh:
                    output = self.output_dir(f'{group}/{droplet.name}')
                    sftp = ssh.open_sftp()
                    sftp.get('/tmp/redis-benchmark.txt', f'{output}/redis-benchmark.txt')

    def setup(self):
        super().setup()


if __name__ == "__main__":
    RedisBenchmark().run()
