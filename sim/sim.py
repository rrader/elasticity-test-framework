import random
from datetime import datetime

import numpy
import numpy as np
from matplotlib import pyplot as plt
import networkx as nx
from nxsim import BaseNetworkAgent, NetworkSimulation, BaseLoggingAgent
import seaborn as sns

from .balancer import Balancer, period, number_of_periods, cpu_number_of_states
from .target import TargetNode

random.seed(2)
numpy.random.seed(2)

number_of_nodes = 3
G = nx.star_graph(number_of_nodes)


class AutoScalingAgent(BaseNetworkAgent):
    def __init__(self, environment=None, agent_id=0, state=()):
        super().__init__(environment=environment, agent_id=agent_id, state=state)
        self.strategy = None

    def run(self):
        if self.state['id'] == 'balancer':
            self.strategy = Balancer(self)
            yield from self.strategy.generate_traffic()
        if self.state['id'] == 'node':
            self.strategy = TargetNode(self)
            yield from self.strategy.process_traffic()

    def get_active_nodes(self):
        nodes = self.get_neighboring_agents(state_id='node')
        active_nodes = [node for node in nodes if node.state['active']]
        return active_nodes

    def get_nodes(self):
        nodes = self.get_neighboring_agents(state_id='node')
        return nodes


# Initialize agent states. Let's assume everyone is normal.
# Add keys as as necessary, but "id" must always refer to that state category
init_states = [{
    'id': 'node',
    'active': False,
    'queue': 0,
    'cpu': 0,
    'dropped': 0,
} for _ in range(number_of_nodes + 1)]

# Seed a balancer
init_states[0] = {'id': 'balancer', 'req_new': 0}
# Activate single node
init_states[1]['active'] = True


sim = NetworkSimulation(topology=G, states=init_states, agent_type=AutoScalingAgent,
                        max_time=period * number_of_periods, dir_path='sim_01', num_trials=1, logging_interval=1.0)

sim.run_simulation()

trial = BaseLoggingAgent.open_trial_state_history(dir_path='sim_01', trial_id=0)

# plt.interactive(False)
# req_num = [sum([state['req_new'] for node_id, state in g.items() if state['id'] == 'balancer']) for t, g in trial.items()  if t > (period * (number_of_periods - 1))]
# plt.plot(req_num)
# plt.show()

# queue_size = [sum([state['queue'] for node_id, state in g.items() if state['id'] == 'node']) for t, g in trial.items()]
# plt.plot(queue_size)
# plt.show()

# cpu_1 = [sum([state['cpu'] for node_id, state in g.items() if state['id'] == 'node' and node_id == 1]) for t, g in trial.items()]
# plt.plot(cpu_1)
# plt.show()
plt.figure(figsize=(15, 15))
plt.figure(1)
plt.subplot(331)
active_nodes = [sum([1 for node_id, state in g.items() if state['id'] == 'node' and state['active']]) for t, g in trial.items() if t > (period * (number_of_periods - 1))]
plt.plot(active_nodes, label='nodes')
plt.legend()

plt.subplot(332)
cpu = [np.mean([state['cpu'] for node_id, state in g.items() if state['id'] == 'node' and state['active']]) for t, g in trial.items() if t > (period * (number_of_periods - 1))]
plt.plot(cpu, label='cpu')
plt.legend()

plt.subplot(335)
dropped = [np.mean([state['dropped'] for node_id, state in g.items() if state['id'] == 'node' and state['active']]) for t, g in trial.items() if t > (period * (number_of_periods - 1))]
plt.plot(dropped, label='dropped')
plt.legend()

plt.subplot(338)
queue = [np.mean([state['last_queue_size'] for node_id, state in g.items() if state['id'] == 'node' and state['active']]) for t, g in trial.items() if t > (period * (number_of_periods - 1))]
plt.plot(queue, label='queue size avg')
plt.legend()
# plt.legend('CPU')
plt.subplot(337)
new_req = [sum([state['req_new'] for node_id, state in g.items() if state['id'] == 'balancer']) for t, g in trial.items() if t > (period * (number_of_periods - 1))]
plt.plot(new_req, label='req_new')
plt.legend()
# plt.legend('CPU')

plt.subplot(334)
u_val = [sum([state['u'] for node_id, state in g.items() if state['id'] == 'balancer']) for t, g in trial.items() if t > (period * (number_of_periods - 1))]
plt.plot(u_val, label='u')

u_val = [sum([state['u1'] for node_id, state in g.items() if state['id'] == 'balancer']) for t, g in trial.items() if t > (period * (number_of_periods - 1))]
plt.plot(u_val, label='u1 cpu', linestyle='dotted')
u_val = [sum([state['u2'] for node_id, state in g.items() if state['id'] == 'balancer']) for t, g in trial.items() if t > (period * (number_of_periods - 1))]
plt.plot(u_val, label='u2 nodes', linestyle='dotted')
u_val = [sum([state['u3'] for node_id, state in g.items() if state['id'] == 'balancer']) for t, g in trial.items() if t > (period * (number_of_periods - 1))]
plt.plot(u_val, label='u3 drop', linestyle='dotted')
# plt.legend('U')

rew = [sum([state['reward'] for node_id, state in g.items() if state['id'] == 'balancer']) for t, g in trial.items() if t > (period * (number_of_periods - 1))]
plt.plot(rew, label='reward', linestyle='dashed')
plt.legend()
plt.show()

balancer = [node['agent'] for node in sim.env.G.nodes.values() if node['agent'].state['id'] == 'balancer'][0]


def build_map(action):
    return np.array([
        [
            balancer.strategy.scaling.agent.q_func[(nodes, cpu)][action]
            for nodes in range(1, number_of_nodes + 1)
        ]
        for cpu in range(cpu_number_of_states + 1)
    ])


def build_policy():
    MAP = {
        'UP': 1.0,
        'DOWN': -1.0,
        'NONE': 0,
        None: 0,
    }
    return np.array([
        [
            MAP[
                max([(val, key) for key, val in balancer.strategy.scaling.agent.q_func[(nodes, cpu)].items()])[1]
            ]
            for nodes in range(1, number_of_nodes + 1)
        ]
        for cpu in range(cpu_number_of_states + 1)
    ])

q_up = build_map('UP')
q_down = build_map('DOWN')
q_none = build_map('NONE')
vmax = numpy.max([numpy.max(q_up), numpy.max(q_down), numpy.max(q_none)])
vmin = -10  # numpy.min([numpy.min(q_up), numpy.min(q_down), numpy.min(q_none)])
plt.subplot(333)
plt.title('Scale Up')
sns.heatmap(q_up, cmap='RdBu', center=0.0, vmax=vmax, vmin=vmin, annot=True)
plt.show()
plt.subplot(336)
plt.title('No Action')
sns.heatmap(q_none, cmap='RdBu', center=0.0, vmax=vmax, vmin=vmin, annot=True)
plt.show()
plt.subplot(339)
plt.title('Scale Down')
sns.heatmap(q_down, cmap='RdBu', center=0.0, vmax=vmax, vmin=vmin, annot=True)

plt.savefig('last.png')
plt.savefig('_{}.png'.format(datetime.now().timestamp()))

plt.figure(2)
plt.title('Policy')
sns.heatmap(build_policy(), cmap='RdBu', center=0.0, vmax=1, vmin=-1, cbar_kws={'label': 'DOWN ... NONE ... UP'})
plt.savefig('policy.png')

plt.figure(3)
nx.draw_networkx(G)
plt.savefig('network.png')
