import os


def envvar_get_int(var_name, default):
    """
    Grab an environment variable and return it as an integer.
    If the environment variable does not exist, return the default.
    """
    return int(os.environ.get(var_name, default))


def batch(batchable, batch_size=1):
    """
    Utility to facilitate batched iteration over a list.

    Arguments:
        batchable (list): The list to break into batches.

    Yields:
        list
    """
    batchable_list = list(batchable)
    length = len(batchable_list)
    for index in range(0, length, batch_size):
        yield batchable_list[index:index + batch_size]
