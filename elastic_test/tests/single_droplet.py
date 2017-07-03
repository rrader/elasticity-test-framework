from time import sleep

from elastic_test.setups.base import BaseExperiment
from elastic_test.setups.metrics import MetricsSetup


class SingleDroplet(MetricsSetup, BaseExperiment):
    """
    Experiment starts a single machine with metrics module setup,
    and measures the metrics for 30 seconds
    """
    LAYOUT = {
        'groups': {
            'Target': {
                'number': 1,
                'assets': ['metrics']
            },
        }
    }

    def experiment(self):
        sleep(30)

    def before_experiment(self):
        super().before_experiment()

    def after_experiment(self):
        super().after_experiment()

    def collect(self):
        super().collect()

    def setup(self):
        super().setup()


if __name__ == "__main__":
    SingleDroplet().run()
