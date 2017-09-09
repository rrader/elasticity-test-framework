import json

from python_hosts import Hosts, HostsEntry

LAYOUT_JSON = '/opt/layout.json'


def main():
    hosts = Hosts(path='/etc/hosts')

    layout = json.load(open(LAYOUT_JSON))
    for name, config in layout.get('groups', {}).items():
        for i, ip in enumerate(config.get('ips', [])):
            host = '{}.{}'.format(i, name).lower()

            hosts.remove_all_matching(name=host)

            new_entry = HostsEntry(entry_type='ipv4', address=ip, names=[host])
            hosts.add([new_entry])
            hosts.write()


if __name__ == '__main__':
    main()
