import os
from time import sleep, time

from elastic_test.base import script
from elastic_test.do_base import LayoutedBase, wait_until_done


class SourceAndTarget(LayoutedBase):
    LAYOUT = {
        'groups': {
            'Target': {
                'number': 1,
                'assets': ['scripts/metrics.sh', 'scripts/metrics.ini']
            },
        }
    }

    def run(self):
        super().run()

        for droplet in self.get_droplet_group('Target'):
            with self.ssh_droplet(droplet) as ssh:
                self.setup(ssh)

        self.before_experiment()
        self.experiment()
        self.after_experiment()

        self.collect()

    def experiment(self):
        sleep(30)

    def before_experiment(self):
        for droplet in self.get_droplet_group('Target'):
            with self.ssh_droplet(droplet) as ssh:
                ssh.exec_command('rm -f /var/log/metrics.sh.log')
                ssh.exec_command('service metrics.sh start')
                sleep(30)
                ssh.exec_command('service metrics.sh stop')

    def after_experiment(self):
        for droplet in self.get_droplet_group('Target'):
            with self.ssh_droplet(droplet) as ssh:
                ssh.exec_command('service metrics.sh stop')

    def collect(self):
        for droplet in self.get_droplet_group('Target'):
            with self.ssh_droplet(droplet) as ssh:
                now = time()
                output = f'output/{now}/Target/{droplet.name}'
                os.makedirs(output)
                sftp = ssh.open_sftp()
                sftp.get('/var/log/metrics.sh.log', f'{output}/metrics.sh.log')

    def setup(self):
        for droplet in self.get_droplet_group('Target'):
            with self.ssh_droplet(droplet) as ssh:
                stdin, stdout, stderr = ssh.exec_command('bash /opt/test/assets/scripts/metrics.sh')
                print(stdout.read().decode(), stderr.read().decode())


if __name__ == "__main__":
    SourceAndTarget().run()
