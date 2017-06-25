import configparser


def read_config():
    config = configparser.ConfigParser()
    config.read('config.ini')
    return config


def script(name):
    lines = open(f'assets/{name}').readlines()
    return lines


class Base:
    def __init__(self):
        self.config = read_config()
