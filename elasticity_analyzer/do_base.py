import json
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
        self.tag = 'PhD'
        self._base_output_dir = self.get_base_output_dir()

    def run(self):
        pass

    def create_droplet(self, tag=None, size='512mb', name=None):
        keys = [self.do_ssh_key()]
        tags = [self.tag]
        if tag:
            tags.append(tag)

        if name is None:
            name = random_name(self.tag)

        droplet = digitalocean.Droplet(
            token=self.token,
            name=name,
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

        if tag is None:
            tag = 'X'

        droplets = self.get_droplet_group(tag)

        to_create = number - len(droplets)
        for n, i in enumerate(range(to_create), start=len(droplets)):
            name = '{}.{}'.format(n, tag.lower())
            droplets.append(
                self.create_droplet(tag, size, name)
            )

        return droplets

    def get_droplet_group(self, tag=None):
        droplets = self.manager.get_all_droplets(tag_name=self.tag)
        if tag:
            droplets = sorted([d for d in droplets if tag in d.tags], key=lambda d: d.name)
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
        return self.ssh(hostname=droplet.ip_address, username='root', compress=True)

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
    DEFAULT_ASSETS = []

    def run(self):
        groups = self.LAYOUT.get('groups', {})

        print('=> Create layout')
        droplets = []
        for name, config in groups.items():
            group_droplets = self.get_or_create_droplet_group(
                name, config.get('number', 1), config.get('size', '512mb')
            )
            droplets.extend(group_droplets)
            self.LAYOUT['groups'][name]['ips'] = [droplet.ip_address for droplet in group_droplets]

        wait_until_done(droplets)

        for name, config in groups.items():
            droplets = self.get_droplet_group(name)
            self.LAYOUT['groups'][name]['ips'] = {droplet.name: droplet.ip_address for droplet in droplets}

        print('=> Populate assets')
        for name, config in groups.items():
            droplets = self.get_droplet_group(name)

            for droplet in droplets:
                with self.ssh_droplet(droplet) as ssh:
                    ssh.exec_command('echo "{}" > /etc/hostname'.format(droplet.name))
                    ssh.exec_command('hostname {}'.format(droplet.name))
                    sftp = ssh.open_sftp()

                    assets = self.DEFAULT_ASSETS + config.get('assets', [])
                    self.LAYOUT['groups'][name]['assets'] = list(assets)
                    for asset in assets:
                        remote_path = f'/opt/test/assets/{asset}'
                        print(f'Putting asset {asset} to {remote_path}')
                        put(sftp, f'assets/{asset}', remote_path)

        layout_txt = json.dumps(self.LAYOUT)
        self.cmd_for_all(f'cat > /opt/layout.json << EOF\n{layout_txt}\nEOF')

        self.asset_script_for_all('setup.sh')
        print('=> Layout created')

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

    def cmd_for_all(self, cmd):
        print(f'Command: {cmd}')
        groups = self.LAYOUT.get('groups', {})
        for name, config in groups.items():
            droplets = self.get_droplet_group(name)

            for droplet in droplets:
                with self.ssh_droplet(droplet) as ssh:
                    stdin, stdout, stderr = ssh.exec_command(cmd)
                    print(stdout.read().decode(), stderr.read().decode())

    def droplets_with_asset(self, asset):
        groups = self.LAYOUT.get('groups', {})
        for name, config in groups.items():
            droplets = self.get_droplet_group(name)

            if asset in config.get('assets', []):
                yield from droplets

    def setup(self):
        pass


if __name__ == "__main__":
    DOBase().run()
