import os
from contextlib import contextmanager
from io import StringIO

import digitalocean
import names
import paramiko
import time
from digitalocean import SSHKey

from elastic_test.base import Base
from elastic_test.utils import mkdir_p, put

SSH_KEY_NAME = 'PhDKey'


def random_name(tag):
    return "{}-{}".format(tag, names.get_full_name()).replace(' ', '-')


def wait_until_done(droplets):
    if not isinstance(droplets, list):
        droplets = [droplets]

    if not droplets:
        return

    print('waiting...')
    for droplet in droplets:
        actions = droplet.get_actions()
        for action in actions:
            action.load()
            action.wait()
    time.sleep(30)


class DOBase(Base):
    def __init__(self):
        super().__init__()
        self.token = self.config['do']['token']
        self.manager = digitalocean.Manager(token=self.token)
        self.tag = 'PhD-1'

    def run(self):
        pass

    def create_droplet(self, tag=None):
        keys = [self.do_ssh_key()]
        tags = [self.tag]
        if tag:
            tags.append(tag)

        droplet = digitalocean.Droplet(
            token=self.token,
            name=random_name(self.tag),
            region='ams2',
            image='ubuntu-14-04-x64',
            size_slug='512mb',
            backups=False,
            ssh_keys=keys,
            tags=tags
        )
        print('creating droplet {}'.format(droplet.name))
        droplet.create()
        return droplet

    def get_or_create_droplet_group(self, tag=None, number=1):
        print('Initialize group "{}" of {} nodes'.format(tag, number))

        droplets = self.get_droplet_group(tag)

        to_create = number - len(droplets)
        for i in range(to_create):
            droplets.append(
                self.create_droplet(tag)
            )

        return droplets

    def get_droplet_group(self, tag=None):
        droplets = self.manager.get_all_droplets(tag_name=self.tag)
        if tag:
            droplets = [d for d in droplets if tag in d.tags]
        for droplet in droplets:
            print('use droplet {}'.format(droplet.name))
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
        now = time.time()
        scenario = self.__class__.__name__
        output = f'output/{scenario}-{now}'
        if subdirectory:
            output = f'{output}/{subdirectory}'
        os.makedirs(output)
        return output


class LayoutedBase(DOBase):
    LAYOUT = {}

    def run(self):
        groups = self.LAYOUT.get('groups', {})

        droplets = []
        for name, config in groups.items():
            group_droplets = self.get_or_create_droplet_group(name, config.get('number', 1))
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

        print('Layout created')


if __name__ == "__main__":
    DOBase().run()
