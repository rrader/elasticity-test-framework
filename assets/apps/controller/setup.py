from setuptools import setup


def main():
    setup(
        name='scaling_controller',
        version="0.1",
        license='BSD',
        author='Roman Rader',
        author_email='roman.rader@gmail.com',
        packages=['scaling_controller', 'metrics_collector'],
        entry_points={
            'console_scripts': ['scaling_controller=scaling_controller:main']
        },
    )


if __name__ == '__main__':
    main()
