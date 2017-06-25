from elastic_test.setups.base import BaseExperiment


class RedisSetup(BaseExperiment):
    def setup(self):
        super().setup()

        for droplet in self.get_droplet_group('Redis'):
            with self.ssh_droplet(droplet) as ssh:
                stdin, stdout, stderr = ssh.exec_command('bash /opt/test/assets/redis/setup.sh')
                print(stdout.read().decode(), stderr.read().decode())

    def before_experiment(self):
        super().before_experiment()
        for droplet in self.get_droplet_group('Redis'):
            with self.ssh_droplet(droplet) as ssh:
                ssh.exec_command('rm -f /var/log/metrics.sh.log')
                ssh.exec_command('service redis start')

    def after_experiment(self):
        super().after_experiment()
        for droplet in self.get_droplet_group('Redis'):
            with self.ssh_droplet(droplet) as ssh:
                ssh.exec_command('service redis stop')
