from setuptools import setup


def main():
    setup(
        name='metricsagent',
        version="0.1",
        license='BSD',
        author='Roman Rader',
        author_email='roman.rader@gmail.com',
        packages=['metricsagent'],
        entry_points={
            'console_scripts': ['metricsagent=metricsagent:main']
        },
    )


if __name__ == '__main__':
    main()
