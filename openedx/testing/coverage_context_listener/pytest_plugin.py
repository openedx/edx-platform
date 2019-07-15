from pavelib.utils.envs import Env
import pytest
import requests

class ContextPlugin(object):
    def __init__(self, config):
        self.config = config
        self.active = config.getoption("pytest-contexts")

    def pytest_runtest_setup(self, item):
        self.doit(item, "setup")

    def pytest_runtest_teardown(self, item):
        self.doit(item, "teardown")

    def pytest_runtest_call(self, item):
        self.doit(item, "call")

    def doit(self, item, when):
        if self.active:
            for server, cfg in Env.BOK_CHOY_SERVERS.items():
                result = requests.post(
                    'http://{host}:{port}/coverage_context/update_context'.format(**cfg),
                    {
                        'item': item.nodeid,
                        'when': when,
                    }
                )
                print(result)
                assert result.status_code == 204


@pytest.hookimpl(tryfirst=True)
def pytest_configure(config):
    config.pluginmanager.register(ContextPlugin(config), "contextplugin")


def pytest_addoption(parser):
    group = parser.getgroup("general")
    group.addoption(
        "--pytest-contexts",
        action="store_true",
        dest="pytest-contexts",
        help="Capture the pytest contexts that coverage is being captured in",
    )
