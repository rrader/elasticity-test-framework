import re
import matplotlib.pyplot as plt
from os.path import basename


def plot_httperf(app, files, output):
    print('plot: httperf')
    data = []
    x = []
    for f in files:
        rate = int(re.search('\d+', basename(f)).group())
        logs = open(f).readlines()

        total = [l for l in logs if 'Total:' in l][0]

        requests = int(re.search('connections (\d+)', total).group(1))
        replies = int(re.search('replies (\d+)', total).group(1))
        sla = replies / requests
        data.append(sla)
        x.append(rate)

    plt.plot(x, data, 'r--')
    plt.ylim(ymin=0, ymax=1.1)
    plt.savefig(f'{output}/httperf.sla.png')
    plt.close()


if __name__ == "__main__":
    output = (
        '/home/roma/Documents/PhD/Science/experiments/elasticity-mode-test-framework/output/'
    )
    files = [
        output + 'BlogInMemory-1504363797.1197114/Source/PhD-1-Guillermo-Esparza/httperf-200.log',
        output + 'BlogInMemory-1504363797.1197114/Source/PhD-1-Guillermo-Esparza/httperf-300.log',
        output + 'BlogInMemory-1504363797.1197114/Source/PhD-1-Guillermo-Esparza/httperf-400.log',
        output + 'BlogInMemory-1504363797.1197114/Source/PhD-1-Guillermo-Esparza/httperf-490.log',
    ]
    from elasticity_analyzer.experiments.blog_balancer import BlogInMemory
    plot_httperf(BlogInMemory(), files, output + 'BlogInMemory-1504363797.1197114/Source/PhD-1-Guillermo-Esparza/')
