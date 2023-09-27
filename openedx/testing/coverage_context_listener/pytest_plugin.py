"""
A pytest plugin that reports test contexts to coverage running in another process.
"""

import pytest


class RemoteContextPlugin:
    """
    Pytest plugin for reporting pytests contexts to coverage running in another process
    """
    def __init__(self, config):
        self.config = config
        self.active = config.getoption("pytest-contexts")

    def pytest_runtest_setup(self, item):
        self.doit(item, "setup")

    def pytest_runtest_teardown(self, item):
        self.doit(item, "teardown")

    def pytest_runtest_call(self, item):
        self.doit(item, "call")


@pytest.hookimpl(tryfirst=True)
def pytest_configure(config):
    config.pluginmanager.register(RemoteContextPlugin(config), "remotecontextplugin")


def pytest_addoption(parser):
    group = parser.getgroup("coverage")
    group.addoption(
        "--pytest-remote-contexts",
        action="store_true",
        dest="pytest-contexts",
        help="Capture the pytest contexts that coverage is being captured in in another process",
    )
