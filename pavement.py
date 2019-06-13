import os
import sys

from setproctitle import getproctitle, setproctitle

# Ensure that we can import pavelib, and that our copy of pavelib
# takes precedence over anything else installed in the virtualenv.
# In local dev, we usually don't need to do this, because Python
# automatically puts the current working directory on the system path.
# In Jenkins, however, we have multiple copies of the edx-platform repo,
# each of which run "pip install -e ." (as part of requirements/edx/local.in)
# Until we re-run pip install, the other copies of edx-platform could
# take precedence, leading to some very strange results.
sys.path.insert(0, os.path.dirname(__file__))

from pavelib import *


def rename_process():
    """
    Replace "python" in the process name with "py_pav_<command>"
    to make it clear in tools like New Relic Infrastructure and top
    which particular paver command was called.
    """
    old_name = getproctitle()
    if 'paver' in sys.argv[0] and 'py_pav_' not in old_name:
        command_name = sys.argv[1]
        new_name = 'py_pav_{}'.format(command_name)
        setproctitle(old_name.replace('python', new_name, 1))


rename_process()
