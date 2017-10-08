import os

from elasticity_analyzer.do_base import LayoutedBase


class BaseExperiment(LayoutedBase):
    def run(self):
        super().run()

        self.setup()

        self.before_experiment()
        self.experiment()
        self.after_experiment()

        self.collect()

    def setup(self):
        self.asset_script_for_all('setup.sh')

    def before_experiment(self):
        self.asset_script_for_all('before_experiment.sh')

    def experiment(self):
        pass

    def after_experiment(self):
        self.asset_script_for_all('after_experiment.sh')

    def collect(self):
        print('=> Download artifacts')
        for droplet, ssh, group, config in self.iterate_ssh():
            output = self.output_dir(f'{group}/{droplet.name}')
            sftp = ssh.open_sftp()
            for asset in config.get('assets', []):
                artifacts = f'assets/{asset}/artifacts.txt'
                if os.path.exists(artifacts):
                    with open(artifacts) as f:
                        for artifact in f.readlines():
                            if not artifact:
                                continue
                            remote_path, local_name = artifact.split(':')
                            print(f'  downloading {remote_path}')
                            sftp.get(remote_path, f'{output}/{local_name}')
