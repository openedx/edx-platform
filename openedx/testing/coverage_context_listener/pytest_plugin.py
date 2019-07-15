from pavelib.utils.envs import Env
import requests

def pytest_runtest_setup(item):
    doit(item, "setup")

def pytest_runtest_teardown(item):
    doit(item, "teardown")

def pytest_runtest_call(item):
    doit(item, "call")

def doit(item, when):
    for server, cfg in Env.BOK_CHOY_SERVERS.items():
        print(
            'http://{host}:{port}/coverage_context/update_context'.format(**cfg)
        )
        result = requests.post(
            'http://{host}:{port}/coverage_context/update_context'.format(**cfg),
            {
                'item': item,
                'when': when,
            }
        )
        print(result)
        assert result.status_code == 200
