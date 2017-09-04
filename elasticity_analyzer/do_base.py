import os
from contextlib import contextmanager, ExitStack
from io import StringIO

import digitalocean
import names
import paramiko
import time
from digitalocean import SSHKey

from elasticity_analyzer.base import Base
from elasticity_analyzer.utils import mkdir_p, put

SSH_KEY_NAME = 'PhDKey'


def random_name(tag):
    return "{}-{}".format(tag, names.get_full_name()).replace(' ', '-')


def wait_until_done(droplets):
    if not isinstance(droplets, list):
        droplets = [droplets]

    if not droplets:
        return

    print('waiting...')
    n = 0
    for droplet in droplets:
        actions = droplet.get_actions()
        for action in actions:
            action.load()
            if action.status != 'completed':
                action.wait()
                n += 1
    if n:
        time.sleep(30)


class DOBase(Base):
    def __init__(self):
        super().__init__()
        self.token = self.config['do']['token']
        self.manager = digitalocean.Manager(token=self.token)
        self.tag = 'PhD-1'
        self._base_output_dir = self.get_base_output_dir()

    def run(self):
        pass

    def create_droplet(self, tag=None, size='512mb'):
        keys = [self.do_ssh_key()]
        tags = [self.tag]
        if tag:
            tags.append(tag)

        droplet = digitalocean.Droplet(
            token=self.token,
            name=random_name(self.tag),
            region='ams2',
            image='ubuntu-14-04-x64',
            size_slug=size,
            backups=False,
            ssh_keys=keys,
            tags=tags
        )
        print('creating droplet {}'.format(droplet.name))
        droplet.create()
        return droplet

    def get_or_create_droplet_group(self, tag=None, number=1, size='512mb'):
        print('Initialize group "{}" of {} nodes'.format(tag, number))

        droplets = self.get_droplet_group(tag)

        to_create = number - len(droplets)
        for i in range(to_create):
            droplets.append(
                self.create_droplet(tag, size)
            )

        return droplets

    def get_droplet_group(self, tag=None):
        droplets = self.manager.get_all_droplets(tag_name=self.tag)
        if tag:
            droplets = [d for d in droplets if tag in d.tags]
        for droplet in droplets:
            print('use droplet {} {}'.format(droplet.name, droplet.ip_address))
        return droplets

    def destroy_all(self):
        droplets = self.manager.get_all_droplets(tag_name=self.tag)
        for droplet in droplets:
            print('destroying droplet {}'.format(droplet.name))
            droplet.destroy()

    @contextmanager
    def ssh(self, **kwargs):
        pkey = paramiko.RSAKey.from_private_key(StringIO(self.config['ssh']['private']))
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(**kwargs, pkey=pkey)
        try:
            yield ssh
        finally:
            ssh.close()
        return ssh

    def ssh_droplet(self, droplet):
        return self.ssh(hostname=droplet.ip_address, username='root')

    @contextmanager
    def ssh_droplet_group(self, group):
        with ExitStack() as stack:
            sshs = []
            for droplet in self.get_droplet_group(group):
                sshs.append(
                    stack.enter_context(self.ssh_droplet(droplet))
                )
            yield sshs

    def do_ssh_key(self):
        all_key = self.manager.get_all_sshkeys()
        for key in all_key:
            if key.name == SSH_KEY_NAME:
                return key

        key = SSHKey(
            token=self.token,
            name=SSH_KEY_NAME,
            public_key=self.config['ssh']['public'],
        )
        key.create()
        return key

    def output_dir(self, subdirectory=None):
        output = self._base_output_dir
        if subdirectory:
            output = f'{output}/{subdirectory}'
        os.makedirs(output, exist_ok=True)
        return output

    def get_base_output_dir(self):
        now = time.time()
        scenario = self.__class__.__name__
        output = f'output/{scenario}-{now}'
        return output


class LayoutedBase(DOBase):
    LAYOUT = {}

    def run(self):
        groups = self.LAYOUT.get('groups', {})

        droplets = []
        for name, config in groups.items():
            group_droplets = self.get_or_create_droplet_group(
                name, config.get('number', 1), config.get('size', '512mb')
            )
            droplets.extend(group_droplets)

        wait_until_done(droplets)

        for name, config in groups.items():
            droplets = self.get_droplet_group(name)

            for droplet in droplets:
                with self.ssh_droplet(droplet) as ssh:
                    sftp = ssh.open_sftp()

                    for asset in config.get('assets', []):
                        remote_path = f'/opt/test/assets/{asset}'
                        print(f'Putting asset {asset} to {remote_path}')
                        put(sftp, f'assets/{asset}', remote_path)

        self.asset_script_for_all('setup.sh')
        print('Layout created')

    def asset_script(self, ssh, asset, script):
        remote_path = f'/opt/test/assets/{asset}'
        print(f'  run {script} on asset {asset}')
        stdin, stdout, stderr = ssh.exec_command(
            f'cd {remote_path}; [ -f {script} ] && bash {script}; cd -'
        )
        print(stdout.read().decode(), stderr.read().decode())

    def asset_script_for_all(self, script):
        print(f'Asset script: {script}')
        groups = self.LAYOUT.get('groups', {})
        for name, config in groups.items():
            droplets = self.get_droplet_group(name)

            for droplet in droplets:
                with self.ssh_droplet(droplet) as ssh:
                    for asset in config.get('assets', []):
                        self.asset_script(ssh, asset, script)

    def droplets_with_asset(self, asset):
        groups = self.LAYOUT.get('groups', {})
        for name, config in groups.items():
            droplets = self.get_droplet_group(name)

            if asset in config.get('assets', []):
                yield from droplets


if __name__ == "__main__":
    DOBase().run()
