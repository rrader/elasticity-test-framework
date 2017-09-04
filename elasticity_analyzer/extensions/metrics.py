import numpy as np

import matplotlib.pyplot as plt


def plot_metric(log, metric, output, ymax=None):
    metric_rows = (l for l in open(log).readlines() if l.startswith(metric))
    data = [float(row.split(' ')[1]) for row in metric_rows]
    x = np.arange(0, len(data))
    plt.plot(x, data, 'r--')
    plt.ylim(ymin=0, ymax=ymax)
    plt.savefig(output)
    plt.close()


def collect_metrics(app):
    print('collect: metrics')
    for group, config in app.LAYOUT.get('groups', {}).items():
        for droplet in app.get_droplet_group(group):
            if 'metrics' in config.get('assets', []):
                with app.ssh_droplet(droplet) as ssh:
                    output = app.output_dir(f'{group}/{droplet.name}')
                    sftp = ssh.open_sftp()
                    sftp.get('/var/log/metrics.sh.log', f'{output}/metrics.sh.log')
                    plot_metric(f'{output}/metrics.sh.log', 'cpu:', f'{output}/metrics.sh.cpu.png', 100)
                    plot_metric(f'{output}/metrics.sh.log', 'memory:', f'{output}/metrics.sh.memory.png')
                    plot_metric(f'{output}/metrics.sh.log', 'network_io.in:', f'{output}/metrics.sh.network_io.in.png')
                    plot_metric(f'{output}/metrics.sh.log', 'network_io.out:', f'{output}/metrics.sh.network_io.out.png')
                    plot_metric(f'{output}/metrics.sh.log', 'disk_usage:', f'{output}/metrics.sh.disk_usage.png')
                    plot_metric(f'{output}/metrics.sh.log', 'fd.allocated:', f'{output}/metrics.sh.fd.allocated.png')
                    plot_metric(f'{output}/metrics.sh.log', 'fd.max:', f'{output}/metrics.sh.fd.max.png')
                    plot_metric(f'{output}/metrics.sh.log', 'tcp_backlog.recv:', f'{output}/metrics.sh.tcp_backlog.recv.png')
                    plot_metric(f'{output}/metrics.sh.log', 'tcp_backlog.send:', f'{output}/metrics.sh.tcp_backlog.send.png')
                    plot_metric(f'{output}/metrics.sh.log', 'cs.vol:', f'{output}/metrics.sh.cs.vol.png')
                    plot_metric(f'{output}/metrics.sh.log', 'cs.nonvol:', f'{output}/metrics.sh.cs.nonvol.png')
                    plot_metric(f'{output}/metrics.sh.log', 'cs.sum:', f'{output}/metrics.sh.cs.sum.png')


if __name__ == "__main__":
    output = (
        '/home/roma/Documents/PhD/elasticity-mode-test-framework/output/'
        'BlogInMemory-1498990479.642404/Target/PhD-1-James-Hunter'
    )
    plot_metric(f'{output}/metrics.sh.log', 'cpu:', f'{output}/metrics.sh.cpu.png')
    plot_metric(f'{output}/metrics.sh.log', 'memory:', f'{output}/metrics.sh.memory.png')
    plot_metric(f'{output}/metrics.sh.log', 'network_io.in:', f'{output}/metrics.sh.network_io.in.png')
    plot_metric(f'{output}/metrics.sh.log', 'network_io.out:', f'{output}/metrics.sh.network_io.out.png')
    plot_metric(f'{output}/metrics.sh.log', 'disk_usage:', f'{output}/metrics.sh.disk_usage.png')
