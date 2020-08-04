from contextlib import contextmanager


@contextmanager
def does_not_raise():
    """A no-op context manager to check if no exception is raised in a pytest"""
    # TODO Once code is upgraded to python 3 delete this function and use its alternate `pytest.does_not_raise()`
    #  or as defined in https://github.com/pytest-dev/pytest/pull/4682#issuecomment-458616795
    yield
