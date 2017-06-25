from elastic_test.do_base import LayoutedBase


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
        pass

    def experiment(self):
        pass

    def after_experiment(self):
        pass

    def collect(self):
        pass
