import json
import os
import tarfile
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
    print(n, 'operations pending')
    if n:
        time.sleep(30)
    print('continue')


class DOBase(Base):
    def __init__(self):
        super().__init__()
        self.token = self.config['do']['token']
        self.manager = digitalocean.Manager(token=self.token)
        self.tag = 'PhD'
        self._base_output_dir = self.get_base_output_dir()
        self._ssh_connections = {}

    def start(self):
        try:
            self.run()
        finally:
            self.close_ssh()

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
        return droplets

    def destroy_all(self):
        droplets = self.manager.get_all_droplets(tag_name=self.tag)
        for droplet in droplets:
            print('destroying droplet {}'.format(droplet.name))
            droplet.destroy()

    def ssh(self, **kwargs):
        cache_key = tuple(sorted(kwargs.items()))
        if self._ssh_connections.get(cache_key):
            return self._ssh_connections[cache_key]
        else:
            pkey = paramiko.RSAKey.from_private_key(StringIO(self.config['ssh']['private']))
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(**kwargs, pkey=pkey)
            self._ssh_connections[cache_key] = ssh
            print('connected to {}'.format(kwargs))
            return ssh

    def ssh_droplet(self, droplet):
        ip_addr = droplet.ip_address
        print('use droplet {} {}'.format(droplet.name, ip_addr))
        return self.ssh(hostname=ip_addr, username='root', compress=True)

    def ssh_droplet_group(self, group):
        sshs = []
        for droplet in self.get_droplet_group(group):
            sshs.append(self.ssh_droplet(droplet))
        return sshs

    def close_ssh(self):
        for key, connection in self._ssh_connections.items():
            connection.close()
        print('connections closed')

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
        self.build_cluster()

    def build_cluster(self):
        groups = self.LAYOUT.get('groups', {})
        print('=> Create layout')

        print('  create droplets')
        droplets = []
        for name, config in groups.items():
            group_droplets = self.get_or_create_droplet_group(
                name, config.get('number', 1), config.get('size', '512mb')
            )
            droplets.extend(group_droplets)
            self.LAYOUT['groups'][name]['ips'] = [droplet.ip_address for droplet in group_droplets]
        wait_until_done(droplets)

        print('  collect IP addresses')
        for name, config in groups.items():
            droplets = self.get_droplet_group(name)
            self.LAYOUT['groups'][name]['ips'] = {droplet.name: droplet.ip_address for droplet in droplets}
            self.LAYOUT['groups'][name]['assets'] = list(self.DEFAULT_ASSETS + config.get('assets', []))

        print('  set hostnames')
        for droplet, ssh, group, config in self.iterate_ssh():
            ssh.exec_command('echo "{}" > /etc/hostname'.format(droplet.name))
            ssh.exec_command('hostname {}'.format(droplet.name))

        self.populate_assets()

        layout_txt = json.dumps(self.LAYOUT)
        self.cmd_for_all(f'cat > /opt/layout.json << EOF\n{layout_txt}\nEOF')
        print('=> Layout created')

    def populate_assets(self):
        print('=> Populate assets')

        if os.path.exists('assets.tgz'):
            os.remove('assets.tgz')
        with tarfile.open('assets.tgz', "w:gz") as tar:
            tar.add('assets')

        for droplet, ssh, group, config in self.iterate_ssh():
            sftp = ssh.open_sftp()
            put(sftp, 'assets.tgz', '/opt/test/assets.tgz')
            ssh.exec_command('cd /opt/test/; rm -rf assets; tar xf assets.tgz; cd -')

    def asset_script(self, ssh, asset, script):
        remote_path = f'/opt/test/assets/{asset}'
        print(f'  run {script} on asset {asset}')
        stdin, stdout, stderr = ssh.exec_command(
            f'cd {remote_path}; [ -f {script} ] && bash {script}; cd -'
        )
        print(stdout.read().decode(), stderr.read().decode())

    def asset_script_for_all(self, script):
        print(f'Asset script: {script}')
        for droplet, ssh, group, config in self.iterate_ssh():
            for asset in config.get('assets', []):
                self.asset_script(ssh, asset, script)

    def cmd_for_all(self, cmd):
        print(f'Command: {cmd}')
        for droplet, ssh, group, config in self.iterate_ssh():
            stdin, stdout, stderr = ssh.exec_command(cmd)
            print(stdout.read().decode(), stderr.read().decode())

    def droplets_with_asset(self, asset):
        groups = self.LAYOUT.get('groups', {})
        for name, config in groups.items():
            droplets = self.get_droplet_group(name)

            if asset in config.get('assets', []):
                yield from droplets

    def iterate_ssh(self, group=None):
        groups = self.LAYOUT.get('groups', {})
        for name, config in groups.items():
            if group is not None and name != group:
                continue

            droplets = self.get_droplet_group(name)

            for droplet in droplets:
                ssh = self.ssh_droplet(droplet)
                yield droplet, ssh, name, config


if __name__ == "__main__":
    DOBase().start()
