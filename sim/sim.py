import random

import numpy as np
import simple_rl
from matplotlib import pyplot as plt
import networkx as nx
from nxsim import BaseNetworkAgent, NetworkSimulation, BaseLoggingAgent

from balancer import Balancer, period, number_of_periods
from target import TargetNode

number_of_nodes = 3
G = nx.star_graph(number_of_nodes)


# # Just like subclassing a process in SimPy
# class MyAgent(BaseNetworkAgent):
#     def __init__(self, environment=None, agent_id=0, state=()):  # Make sure to have these three keyword arguments
#         super().__init__(environment=environment, agent_id=agent_id, state=state)
#         # Add your own attributes here
#
#     def run(self):
#         # Add your behaviors here


class AutoScalingAgent(BaseNetworkAgent):
    def __init__(self, environment=None, agent_id=0, state=()):
        super().__init__(environment=environment, agent_id=agent_id, state=state)
        self.bite_prob = 0.05

    def run(self):
        if self.state['id'] == 'balancer':
            balancer = Balancer(self)
            yield from balancer.generate_traffic()
        if self.state['id'] == 'node':
            target = TargetNode(self)
            yield from target.process_traffic()

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

# zombie_census = [sum([1 for node_id, state in g.items() if state['id'] == 'node']) for t, g in trial.items()]
# print(trial)
# req_num = [sum([state['req_new'] for node_id, state in g.items() if state['id'] == 'balancer']) for t, g in trial.items()  if t > (period * (number_of_periods - 1))]
# plt.plot(req_num)
# plt.show()

# queue_size = [sum([state['queue'] for node_id, state in g.items() if state['id'] == 'node']) for t, g in trial.items()]
# plt.plot(queue_size)
# plt.show()

# cpu_1 = [sum([state['cpu'] for node_id, state in g.items() if state['id'] == 'node' and node_id == 1]) for t, g in trial.items()]
# plt.plot(cpu_1)
# plt.show()

cpu = [np.mean([state['cpu'] for node_id, state in g.items() if state['id'] == 'node' and state['active']]) for t, g in trial.items() if t > (period * (number_of_periods - 1))]
plt.plot(cpu)
plt.show()

u_val = [sum([state['u'] for node_id, state in g.items() if state['id'] == 'balancer']) for t, g in trial.items() if t > (period * (number_of_periods - 1))]
plt.plot(u_val)
plt.show()
rew = [sum([state['reward'] for node_id, state in g.items() if state['id'] == 'balancer']) for t, g in trial.items() if t > (period * (number_of_periods - 1))]
plt.plot(rew)
plt.show()

active_nodes = [sum([1 for node_id, state in g.items() if state['id'] == 'node' and state['active']]) for t, g in trial.items() if t > (period * (number_of_periods - 1))]
plt.plot(active_nodes)
plt.show()

# nx.draw_networkx(G)
# plt.show()
