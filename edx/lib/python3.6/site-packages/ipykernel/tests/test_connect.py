"""Tests for kernel connection utilities"""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

import json
import os

from traitlets.config import Config
from ipython_genutils.tempdir import TemporaryDirectory, TemporaryWorkingDirectory
from ipython_genutils.py3compat import str_to_bytes
from ipykernel import connect
from ipykernel.kernelapp import IPKernelApp


sample_info = dict(ip='1.2.3.4', transport='ipc',
        shell_port=1, hb_port=2, iopub_port=3, stdin_port=4, control_port=5,
        key=b'abc123', signature_scheme='hmac-md5',
    )


class DummyKernelApp(IPKernelApp):
    def initialize(self, argv=[]):
        self.init_profile_dir()
        self.init_connection_file()


def test_get_connection_file():
    cfg = Config()
    with TemporaryWorkingDirectory() as d:
        cfg.ProfileDir.location = d
        cf = 'kernel.json'
        app = DummyKernelApp(config=cfg, connection_file=cf)
        app.initialize()

        profile_cf = os.path.join(app.connection_dir, cf)
        assert profile_cf == app.abs_connection_file
        with open(profile_cf, 'w') as f:
            f.write("{}")
        assert os.path.exists(profile_cf)
        assert connect.get_connection_file(app) == profile_cf

        app.connection_file = cf
        assert connect.get_connection_file(app) == profile_cf


def test_get_connection_info():
    with TemporaryDirectory() as d:
        cf = os.path.join(d, 'kernel.json')
        connect.write_connection_file(cf, **sample_info)
        json_info = connect.get_connection_info(cf)
        info = connect.get_connection_info(cf, unpack=True)
    assert isinstance(json_info, str)

    sub_info = {k:v for k,v in info.items() if k in sample_info}
    assert sub_info == sample_info

    info2 = json.loads(json_info)
    info2['key'] = str_to_bytes(info2['key'])
    sub_info2 = {k:v for k,v in info.items() if k in sample_info}
    assert sub_info2 == sample_info
