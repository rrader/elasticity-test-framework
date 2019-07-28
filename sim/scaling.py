import numpy as np


class ScalingPolicy:
    def __init__(self, balancer_node):
        self.balancer_node = balancer_node

    def run(self):
        nodes = self.balancer_node.get_active_nodes()
        cpu_avg = np.mean([node.state['cpu'] for node in nodes])
        if cpu_avg > 0.8:
            self._scale_up()
        if cpu_avg < 0.4:
            self._scale_down()

    def _scale_up(self):
        nodes = self.balancer_node.get_neighboring_agents(state_id='node')
        passive_nodes = [node for node in nodes if not node.state['active']]
        if passive_nodes:
            passive_nodes[0].state['active'] = True
            return True
        else:
            return False

    def _scale_down(self):
        nodes = self.balancer_node.get_neighboring_agents(state_id='node')
        active_nodes = [node for node in nodes if node.state['active']]
        if len(active_nodes) > 1:
            active_nodes[0].state['active'] = False
            return True
        else:
            return False
