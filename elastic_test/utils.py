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
