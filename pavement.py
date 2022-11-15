import sys  # lint-amnesty, pylint: disable=django-not-configured, missing-module-docstring
import os

# Ensure that we can import pavelib, and that our copy of pavelib
# takes precedence over anything else installed in the virtualenv.
# In local dev, we usually don't need to do this, because Python
# automatically puts the current working directory on the system path.
# Until we re-run pip install, the other copies of edx-platform could
# take precedence, leading to some very strange results.
sys.path.insert(0, os.path.dirname(__file__))

from pavelib import *  # lint-amnesty, pylint: disable=wildcard-import, wrong-import-position
