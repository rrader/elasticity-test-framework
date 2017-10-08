from elasticity_analyzer.experiments.blog_inmemory import BlogInMemory


class BlogInMemoryWithNginx(BlogInMemory):
    LAYOUT = {
        'groups': {
            'Target': {
                'number': 1,
                'assets': ['metrics', 'apps/blog', 'apps/blog-nginx'],
                'size': '512mb'
            },
            'Source': {
                'number': 1,
                'assets': ['metrics', 'apps/httperf'],
                'size': '512mb'
            },
        }
    }
    TIMEOUT = 0.5  # seconds
    START_RATE = 5
    MAX_RATE = 100
    STEP_DURATION = 30
    STEP_RATE = 5
    PORT = 80

    def __init__(self):
        super().__init__()
        self.files = []

    def experiment(self):
        super().experiment()

    def before_experiment(self):
        super().before_experiment()

    def after_experiment(self):
        super().after_experiment()

    def collect(self):
        super().collect()

    def setup(self):
        super().setup()


if __name__ == "__main__":
    BlogInMemoryWithNginx().start()
