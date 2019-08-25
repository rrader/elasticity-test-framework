from .scaling_q import QScalingPolicy, QScalingPolicyPriorKnowledge, QScalingPolicyPriorKnowledgePotential

number_of_periods = 10
cpu_number_of_states = 9
period = 500
max_requests = 120
cooldown_time = 5
step_size = 5


def traffic_triangular_shape(now):
    period_t = (now + period // 2) % period
    period_t = (period_t // step_size) * step_size
    req_new = int(abs(float(period_t - period // 2) / (period // 2)) * max_requests)
    return req_new


class Balancer:
    policy = QScalingPolicyPriorKnowledgePotential

    def __init__(self, balancer_node):
        self.balancer_node = balancer_node
        self.cooldown = 0
        self._prev_period_id = None
        self.scaling = self.policy(balancer_node)

    def generate_traffic(self):
        balancer = self.balancer_node
        while True:
            balancer.state['period_id'] = balancer.env.now // period
            if self._prev_period_id is not None and self._prev_period_id != balancer.state['period_id']:
                self.scaling.end_of_period()
            self._prev_period_id = balancer.state['period_id']

            req_new = traffic_triangular_shape(balancer.env.now)
            balancer.state['req_new'] = req_new
            self._route_request(req_new)
            if self.cooldown > 0:
                self.cooldown -= 1

            if self.cooldown == 0:
                if self.scaling.run(cooldown=False):
                    self.cooldown = cooldown_time
            else:
                self.scaling.run(cooldown=True)
            yield balancer.env.timeout(1.0)

    def _route_request(self, req_new):
        active_nodes = self.balancer_node.get_active_nodes()
        per_node = req_new // len(active_nodes)
        for node in active_nodes:
            node.state['queue'] += per_node
