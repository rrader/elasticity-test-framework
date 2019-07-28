max_requests_per_tick = 100


class TargetNode:
    def __init__(self, node):
        self.node = node

    def process_traffic(self):
        node = self.node
        while True:
            to_process = min(node.state['queue'], max_requests_per_tick)
            node.state['dropped'] = node.state['queue'] - to_process
            node.state['queue'] = 0
            node.state['cpu'] = float(to_process) / max_requests_per_tick
            yield node.env.timeout(1)
