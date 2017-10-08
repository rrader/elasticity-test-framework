from time import sleep

from elasticity_analyzer.extensions.metrics import collect_metrics
from elasticity_analyzer.setups.base import BaseExperiment


class SingleDroplet(BaseExperiment):
    """
    Experiment starts a single machine with metrics module setup,
    and measures the metrics for 30 seconds
    """
    DEFAULT_ASSETS = ['hosts', 'metrics']
    LAYOUT = {
        'groups': {
            'Target': {
                'number': 1,
                'assets': ['metrics/agent']
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
        collect_metrics(self)

    def setup(self):
        super().setup()


if __name__ == "__main__":
    SingleDroplet().start()
