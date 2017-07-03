import os


def mkdir_p(sftp, remote, is_dir=False):
    """
    emulates mkdir_p if required.
    sftp - is a valid sftp object
    remote - remote path to create.
    """
    dirs_ = []
    if is_dir:
        dir_ = remote
    else:
        dir_, basename = os.path.split(remote)
    while len(dir_) > 1:
        dirs_.append(dir_)
        dir_, _ = os.path.split(dir_)

    if len(dir_) == 1 and not dir_.startswith("/"):
        dirs_.append(dir_) # For a remote path like y/x.txt

    while len(dirs_):
        dir_ = dirs_.pop()
        try:
            sftp.stat(dir_)
        except:
            print("making ... dir",  dir_)
            sftp.mkdir(dir_)


def put_dir(sftp, source, target):
    assert os.path.isdir(source)
    ignore = []
    if os.path.exists(f'{source}/.ignore'):
        ignore = open(f'{source}/.ignore').readlines()

    for item in os.listdir(source):
        if item in ignore:
            print(f' ignoring {source}/{item}')
            continue
        put(sftp, os.path.join(source, item), '%s/%s' % (target, item))


def put(sftp, local_path, remote_path):
    if os.path.isfile(local_path):
        mkdir_p(sftp, remote_path, is_dir=False)
        print(f' {local_path} to {remote_path}...')
        sftp.put(local_path, remote_path)
    else:
        mkdir_p(sftp, remote_path, is_dir=True)
        put_dir(sftp, local_path, remote_path)
