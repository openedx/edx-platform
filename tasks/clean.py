from __future__ import print_function

import os
import sys
from distutils.spawn import find_executable

from path import path
from invoke import task, Collection
from invoke import run as sh
try:
    from pygments.console import colorize
except ImportError:
    colorize = lambda color, text: text
from .utils.cmd import cmd
from .utils.envs import Env
from .i18n import I18N_REPORT_DIR

ns = Collection()


@task
def clean_reports_dir():
    """Clean coverage files, to ensure that we don't use stale data to generate reports."""
    I18N_REPORT_DIR.rmtree_p()
    I18N_REPORT_DIR.makedirs_p()

ns.add_task(clean_reports_dir, "reports")
