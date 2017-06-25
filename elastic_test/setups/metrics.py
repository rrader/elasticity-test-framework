from time import sleep

from elastic_test.setups.base import BaseExperiment


class MetricsSetup(BaseExperiment):
    def setup(self):
        super().setup()
        for group in self.LAYOUT.get('groups', {}):
            for droplet in self.get_droplet_group(group):
                with self.ssh_droplet(droplet) as ssh:
                    stdin, stdout, stderr = ssh.exec_command('bash /opt/test/assets/metrics/metrics.sh')
                    print(stdout.read().decode(), stderr.read().decode())

    def before_experiment(self):
        super().before_experiment()
        for group in self.LAYOUT.get('groups', {}):
            for droplet in self.get_droplet_group(group):
                with self.ssh_droplet(droplet) as ssh:
                    ssh.exec_command('rm -f /var/log/metrics.sh.log')
                    ssh.exec_command('service metrics.sh start')

    def after_experiment(self):
        super().after_experiment()
        sleep(10)
        for group in self.LAYOUT.get('groups', {}):
            for droplet in self.get_droplet_group(group):
                with self.ssh_droplet(droplet) as ssh:
                    ssh.exec_command('service metrics.sh stop')

    def collect(self):
        super().collect()
        print('collect: metrics')
        for group in self.LAYOUT.get('groups', {}):
            for droplet in self.get_droplet_group(group):
                with self.ssh_droplet(droplet) as ssh:
                    output = self.output_dir(f'{group}/{droplet.name}')
                    sftp = ssh.open_sftp()
                    sftp.get('/var/log/metrics.sh.log', f'{output}/metrics.sh.log')
