from pprint import pprint
from random import random

import numpy as np
from simple_rl.agents import QLearningAgent

from scaling import ScalingPolicy

pressure_cpu_threshold = 0.1


def _reward(policy, nodes, max_node_num):
    cpu_avg = np.mean([node.state['cpu'] for node in nodes])
    dropped = sum([node.state['dropped'] for node in nodes])

    return (
        cpu_avg +
        10 * (1 - len(nodes) / float(max_node_num)) +
        0 if dropped == 0 else -100
    )


def _reward_diff(policy, nodes, max_node_num):
    prev_u = policy.data.get('prev_u', 0.0)
    cpu_avg = np.mean([node.state['cpu'] for node in nodes])
    dropped = sum([node.state['dropped'] for node in nodes])
    # pressure = -10 * (1 - cpu_avg) if cpu_avg > pressure_cpu_threshold else 10.

    u = (
        10 ** cpu_avg +
        10 * (1 - len(nodes) / float(max_node_num)) +
        1 if dropped == 0 else -10
    )
    reward = u #(u - prev_u) #+ (0.5 if u >= 0 else -0.5)
    policy.data['prev_u'] = prev_u
    policy.balancer_node.state['u'] = u
    policy.balancer_node.state['reward'] = reward

    return reward


class QScalingPolicy(ScalingPolicy):
    reward = _reward_diff

    def __init__(self, balancer_node):
        super().__init__(balancer_node)
        self.data = {}
        self.agent = QLearningAgent(
            ['NONE', 'UP', 'DOWN'], epsilon=0.1, anneal=True,
            gamma=0.99, alpha=0.1,
        )
        self.default_q = random()
        self.max_node_num = len(self.balancer_node.get_nodes())
        self._impossible = False

    def run(self):
        learn = True
        from balancer import period
        from balancer import number_of_periods
        if self.balancer_node.env.now > (period * (number_of_periods - 2)):
            learn = False
            self.agent.epsilon = 0

        nodes = self.balancer_node.get_active_nodes()

        cpu_avg = np.mean([node.state['cpu'] for node in nodes])
        cpu_state = int(cpu_avg * 6)

        if self._impossible:
            self._impossible = False
            reward = -100
        else:
            reward = self.reward(nodes, self.max_node_num)

        state = (len(nodes), cpu_state)

        action = self.agent.act(state, reward, learning=learn)
        if self.balancer_node.env.now % 100 == 0:
            pprint({
                s: dict(self.agent.q_func[s])
                for s in [(1,0), (1,1), (1,2), (1,3), (1,4), (1,5), (1,6)]
            })
            pprint({
                s: dict(self.agent.q_func[s])
                for s in [(2, 0), (2, 1), (2, 2), (2, 3), (2, 4), (2, 5), (2, 6)]
            })
            pprint({
                s: dict(self.agent.q_func[s])
                for s in [(3, 0), (3, 1), (3, 2), (3, 3), (3, 4), (3, 5), (3, 6)]
            })
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
