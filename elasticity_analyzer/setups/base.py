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
        pass

    def before_experiment(self):
        self.asset_script_for_all('before_experiment.sh')

    def experiment(self):
        pass

    def after_experiment(self):
        self.asset_script_for_all('after_experiment.sh')

    def collect(self):
        pass
