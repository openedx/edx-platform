import os
import nbgrader
import sys
import contextlib


@contextlib.contextmanager
def mock_platform(platform):
    old_platform = sys.platform
    sys.platform = platform
    yield
    sys.platform = old_platform


def test_nbextension_linux():
    from nbgrader import _jupyter_nbextension_paths
    with mock_platform("linux"):
        nbexts = _jupyter_nbextension_paths()
        assert len(nbexts) == 4
        assert nbexts[0]['section'] == 'notebook'
        assert nbexts[1]['section'] == 'tree'
        assert nbexts[2]['section'] == 'notebook'
        assert nbexts[3]['section'] == 'tree'
        paths = [ext['src'] for ext in nbexts]
        for path in paths:
            assert os.path.isdir(os.path.join(os.path.dirname(nbgrader.__file__), path))


def test_nbextension_mac():
    from nbgrader import _jupyter_nbextension_paths
    with mock_platform("darwin"):
        nbexts = _jupyter_nbextension_paths()
        assert len(nbexts) == 4
        assert nbexts[0]['section'] == 'notebook'
        assert nbexts[1]['section'] == 'tree'
        assert nbexts[2]['section'] == 'notebook'
        assert nbexts[3]['section'] == 'tree'
        paths = [ext['src'] for ext in nbexts]
        for path in paths:
            assert os.path.isdir(os.path.join(os.path.dirname(nbgrader.__file__), path))


def test_nbextension_windows():
    from nbgrader import _jupyter_nbextension_paths
    with mock_platform("win32"):
        nbexts = _jupyter_nbextension_paths()
        assert len(nbexts) == 3
        assert nbexts[0]['section'] == 'notebook'
        assert nbexts[1]['section'] == 'tree'
        assert nbexts[2]['section'] == 'notebook'
        paths = [ext['src'] for ext in nbexts]
        for path in paths:
            assert os.path.isdir(os.path.join(os.path.dirname(nbgrader.__file__), path))


def test_serverextension_linux():
    from nbgrader import _jupyter_server_extension_paths
    with mock_platform("linux"):
        serverexts = _jupyter_server_extension_paths()
        assert len(serverexts) == 3
        assert serverexts[0]['module'] == 'nbgrader.server_extensions.formgrader'
        assert serverexts[1]['module'] == 'nbgrader.server_extensions.validate_assignment'
        assert serverexts[2]['module'] == 'nbgrader.server_extensions.assignment_list'


def test_serverextension_mac():
    from nbgrader import _jupyter_server_extension_paths
    with mock_platform("darwin"):
        serverexts = _jupyter_server_extension_paths()
        assert len(serverexts) == 3
        assert serverexts[0]['module'] == 'nbgrader.server_extensions.formgrader'
        assert serverexts[1]['module'] == 'nbgrader.server_extensions.validate_assignment'
        assert serverexts[2]['module'] == 'nbgrader.server_extensions.assignment_list'


def test_serverextension_windows():
    from nbgrader import _jupyter_server_extension_paths
    with mock_platform("win32"):
        serverexts = _jupyter_server_extension_paths()
        assert len(serverexts) == 2
        assert serverexts[0]['module'] == 'nbgrader.server_extensions.formgrader'
        assert serverexts[1]['module'] == 'nbgrader.server_extensions.validate_assignment'
