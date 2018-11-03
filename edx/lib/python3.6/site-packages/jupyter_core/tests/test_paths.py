"""Tests for paths"""

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

import os

try:
    from unittest.mock import patch
except ImportError:
    from mock import patch # py2

from jupyter_core import paths
from jupyter_core.paths import (
    jupyter_config_dir, jupyter_data_dir, jupyter_runtime_dir,
    jupyter_path, ENV_JUPYTER_PATH,
)
from .mocking import darwin, windows, linux

pjoin = os.path.join


xdg_env = {
    'XDG_CONFIG_HOME': '/tmp/xdg/config',
    'XDG_DATA_HOME': '/tmp/xdg/data',
    'XDG_RUNTIME_DIR': '/tmp/xdg/runtime',
}
xdg = patch.dict('os.environ', xdg_env)
no_xdg = patch.dict('os.environ', {
    'XDG_CONFIG_HOME': '',
    'XDG_DATA_HOME': '',
    'XDG_RUNTIME_DIR': '',
})

appdata = patch.dict('os.environ', {'APPDATA': 'appdata'})

no_config_env = patch.dict('os.environ', {
    'JUPYTER_CONFIG_DIR': '',
    'JUPYTER_DATA_DIR': '',
    'JUPYTER_RUNTIME_DIR': '',
    'JUPYTER_PATH': '',
})

jupyter_config_env = '/jupyter-cfg'
config_env = patch.dict('os.environ', {'JUPYTER_CONFIG_DIR': jupyter_config_env})


def realpath(path):
    return os.path.realpath(os.path.expanduser(path))

home_jupyter = realpath('~/.jupyter')


def test_config_dir_darwin():
    with darwin, no_config_env:
        config = jupyter_config_dir()
    assert config == home_jupyter
    
    with darwin, config_env:
        config = jupyter_config_dir()
    assert config == jupyter_config_env


def test_config_dir_windows():
    with windows, no_config_env:
        config = jupyter_config_dir()
    assert config == home_jupyter
    
    with windows, config_env:
        config = jupyter_config_dir()
    assert config == jupyter_config_env


def test_config_dir_linux():
    with windows, no_config_env:
        config = jupyter_config_dir()
    assert config == home_jupyter
    
    with windows, config_env:
        config = jupyter_config_dir()
    assert config == jupyter_config_env


def test_data_dir_env():
    data_env = 'runtime-dir'
    with patch.dict('os.environ', {'JUPYTER_DATA_DIR': data_env}):
        data = jupyter_data_dir()
    assert data == data_env


def test_data_dir_darwin():
    with darwin:
        data = jupyter_data_dir()
    assert data == realpath('~/Library/Jupyter')
    
    with darwin, xdg:
        # darwin should ignore xdg
        data = jupyter_data_dir()
    assert data == realpath('~/Library/Jupyter')


def test_data_dir_windows():
    with windows, appdata:
        data = jupyter_data_dir()
    assert data == pjoin('appdata', 'jupyter')
    
    with windows, appdata, xdg:
        # windows should ignore xdg
        data = jupyter_data_dir()
    assert data == pjoin('appdata', 'jupyter')


def test_data_dir_linux():
    with linux, no_xdg:
        data = jupyter_data_dir()
    assert data == realpath('~/.local/share/jupyter')
    
    with linux, xdg:
        data = jupyter_data_dir()
    assert data == pjoin(xdg_env['XDG_DATA_HOME'], 'jupyter')


def test_runtime_dir_env():
    rtd_env = 'runtime-dir'
    with patch.dict('os.environ', {'JUPYTER_RUNTIME_DIR': rtd_env}):
        runtime = jupyter_runtime_dir()
    assert runtime == rtd_env


def test_runtime_dir_darwin():
    with darwin:
        runtime = jupyter_runtime_dir()
    assert runtime == realpath('~/Library/Jupyter/runtime')
    
    with darwin, xdg:
        # darwin should ignore xdg
        runtime = jupyter_runtime_dir()
    assert runtime == realpath('~/Library/Jupyter/runtime')


def test_runtime_dir_windows():
    with windows, appdata:
        runtime = jupyter_runtime_dir()
    assert runtime == pjoin('appdata', 'jupyter', 'runtime')
    
    with windows, appdata, xdg:
        # windows should ignore xdg
        runtime = jupyter_runtime_dir()
    assert runtime == pjoin('appdata', 'jupyter', 'runtime')


def test_runtime_dir_linux():
    with linux, no_xdg:
        runtime = jupyter_runtime_dir()
    assert runtime == realpath('~/.local/share/jupyter/runtime')
    
    with linux, xdg:
        runtime = jupyter_runtime_dir()
    assert runtime == pjoin(xdg_env['XDG_RUNTIME_DIR'], 'jupyter')


def test_jupyter_path():
    system_path = ['system', 'path']
    with no_config_env, patch.object(paths, 'SYSTEM_JUPYTER_PATH', system_path):
        path = jupyter_path()
    assert path[0] == jupyter_data_dir()
    assert path[-2:] == system_path


def test_jupyter_path_env():
    path_env = os.pathsep.join([
        pjoin('foo', 'bar'),
        pjoin('bar', 'baz', ''), # trailing /
    ])
    
    with patch.dict('os.environ', {'JUPYTER_PATH': path_env}):
        path = jupyter_path()
    assert path[:2] == [pjoin('foo', 'bar'), pjoin('bar', 'baz')]


def test_jupyter_path_sys_prefix():
    with patch.object(paths, 'ENV_JUPYTER_PATH', ['sys_prefix']):
        path = jupyter_path()
    assert 'sys_prefix' in path


def test_jupyter_path_subdir():
    path = jupyter_path('sub1', 'sub2')
    for p in path:
        assert p.endswith(pjoin('', 'sub1', 'sub2'))

