from statistics import mean


def cpu_threshold(env):
    cpu = [instance['cpu'] for instance in env.last_metrics()]
    print(cpu)
    if None in cpu:
        print('No data yet')
        return
    avg = mean(cpu)
    print('avg cpu:', avg)

    env.vars.setdefault('avg_window', [])
    env.vars.get('avg_window').append(avg)
    if len(env.vars.get('avg_window')) > 10:
        del env.vars.get('avg_window')[0]

    if env.vars.get('last_scaled'):
        if env.time() - env.vars.get('last_scaled') < 30:
            print('waiting for 30 sec')
            return

    if len(env.vars.get('avg_window')) == 10:
        avg_window = mean(env.vars.get('avg_window'))
        print('avg 10s window:', avg_window)
        if avg_window >= 90:
            if env.instances + 1 > env.max_instances:
                print('Overload! Maximum instance number exceeded!')
                return
            env.set_instance_number(env.instances + 1)
            env.vars['last_scaled'] = env.time()
