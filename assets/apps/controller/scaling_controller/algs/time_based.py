def time_based(env):
    """Scale in 2 min from start"""
    if env.time() >= 120:
        if not env.vars.get('is_scaled_at_120'):
            env.set_instance_number(2)
            env.vars['is_scaled_at_120'] = True
