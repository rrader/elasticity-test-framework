from collections import defaultdict

import numpy as np
from simple_rl.agents import QLearningAgent

from .scaling import ScalingPolicy

pressure_cpu_threshold = 0.1


def calculate_u(max_node_num, nodes, policy):
    cpu_avg = np.mean([node.state['cpu'] for node in nodes]) + 0.05
    dropped = sum([node.state['dropped'] for node in nodes])

    u1 = 1.0 * cpu_avg
    u2 = 3 * (1 - (len(nodes) - 1) / float(max_node_num - 1))
    u = (
        (u1 + u2)
        if dropped == 0 else
        -dropped
    )
    policy.balancer_node.state['u1'] = u1
    policy.balancer_node.state['u2'] = u2
    policy.balancer_node.state['u3'] = 0
    return u


def _reward(policy, nodes, max_node_num):
    u = calculate_u(max_node_num, nodes, policy)
    policy.balancer_node.state['u'] = u
    policy.balancer_node.state['reward'] = u
    return u


def _reward_diff(policy, nodes, max_node_num):
    prev_u = policy.data.get('prev_u', 0.0)
    u = calculate_u(max_node_num, nodes, policy)

    reward = (u - prev_u) + (0.5 if u >= 0 else -0.5)
    policy.data['prev_u'] = u
    policy.balancer_node.state['u'] = u
    policy.balancer_node.state['reward'] = reward

    return reward


class QScalingPolicy(ScalingPolicy):
    reward = _reward

    def __init__(self, balancer_node):
        super().__init__(balancer_node)

        self.data = {}
        self.agent = QLearningAgent(
            ['NONE', 'UP', 'DOWN'], epsilon=0.3, anneal=True,
            gamma=0.3, alpha=0.2,
            # explore='softmax'
        )
        self._set_q()

        self.max_node_num = len(self.balancer_node.get_nodes())
        self._impossible = False

    def run(self, cooldown):
        from .balancer import cpu_number_of_states

        learn = True
        from .balancer import period
        from .balancer import number_of_periods
        if self.balancer_node.env.now > (period * (number_of_periods - 2)):
            learn = False
            self.agent.epsilon = 0

        nodes = self.balancer_node.get_active_nodes()

        cpu_avg = np.mean([node.state['cpu'] for node in nodes])
        cpu_state = int(cpu_avg * cpu_number_of_states)

        if self._impossible:
            self._impossible = False
            reward = -100
        else:
            reward = self.reward(nodes, self.max_node_num)

        state = (len(nodes), cpu_state)

        # DOCUMENT this cooldown behavior!
        if cooldown:
            self.agent.update(self.agent.prev_state, self.agent.prev_action, reward, state)
            action = 'NONE'
        else:
            action = self.agent.act(state, reward, learning=learn)

        scaled = False
        if action == 'UP':
            if not self._scale_up():
                self._impossible = True
            else:
                scaled = True
        if action == 'DOWN':
            if not self._scale_down():
                self._impossible = True
            else:
                scaled = True
        return scaled

    def end_of_period(self):
        self.agent.end_of_episode()

    def _set_q(self):
        self.agent.q_func = defaultdict(lambda : defaultdict(lambda: 0))


class QScalingPolicyRandomQ(QScalingPolicy):
    def _set_q(self):
        self.agent.q_func = defaultdict(lambda : defaultdict(lambda: np.random.random()))


class QScalingPolicyPriorKnowledge(QScalingPolicy):
    def _set_q(self):
        self.agent.q_func = defaultdict(lambda: defaultdict(lambda: 0.0))
        # prior knowledge
        nodes_max = len(self.balancer_node.get_nodes()) + 1
        from .balancer import cpu_number_of_states
        for cpu in range(cpu_number_of_states + 1):
            for nodes in range(1, nodes_max):
                up = 0
                down = 0
                none = 0.5

                if cpu == 0:
                    down = 1
                if cpu == cpu_number_of_states:
                    up = 1
                if nodes == nodes_max:
                    up = -1
                if nodes == 1:
                    down = -1

                self.agent.q_func[(nodes, cpu)] = {
                    'UP': up,
                    'DOWN': down,
                    'NONE': none,
                    None: 0,
                }


class QScalingPolicyPriorKnowledgePotential(QScalingPolicy):
    def _set_q(self):
        self.agent.q_func = defaultdict(lambda: defaultdict(lambda: 0.0))
        # prior knowledge
        nodes_max = len(self.balancer_node.get_nodes()) + 1
        from .balancer import cpu_number_of_states
        for cpu in range(cpu_number_of_states + 1):
            for nodes in range(1, nodes_max):
                up = 0
                down = 0
                none = 0.5

                if cpu == 0:
                    down = 1
                if cpu == cpu_number_of_states:
                    up = 1
                if nodes == nodes_max:
                    up = -1
                if nodes == 1:
                    down = -1

                self.agent.q_func[(nodes, cpu)] = {
                    'UP': up,
                    'DOWN': down,
                    'NONE': none,
                    None: 0,
                }

        for action in ['UP', 'DOWN', 'NONE']:
            for nodes in range(1, nodes_max):
                row = [
                    self.agent.q_func[(nodes, cpu)][action]
                    for cpu in range(cpu_number_of_states + 1)
                ]
                row_new = [
                    sum(
                        val / (1 + abs(i - j) ** 2)
                        for j, val in enumerate(row)
                    ) for i in range(len(row))
                ]
                for cpu, val in enumerate(row_new):
                    self.agent.q_func[(nodes, cpu)][action] = val
