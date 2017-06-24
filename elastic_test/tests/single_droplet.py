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
                stdin, stdout, stderr = ssh.exec_command('bash /opt/test/assets/scripts/metrics.sh')
                print(stdout.read().decode(), stderr.read().decode())

                ssh.exec_command('rm -f /var/log/metrics.sh.log')
                ssh.exec_command('service metrics.sh start')
                sleep(30)
                ssh.exec_command('service metrics.sh stop')

                now = time()
                output = f'output/{now}/{droplet.name}'
                os.makedirs(output)
                sftp = ssh.open_sftp()
                sftp.get('/var/log/metrics.sh.log', f'{output}/metrics.sh.log')


if __name__ == "__main__":
    SourceAndTarget().run()
