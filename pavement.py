import sys
import os

# Ensure that we can import pavelib, and that our copy of pavelib
# takes precedence over anything else installed in the virtualenv.
# In local dev, we usually don't need to do this, because Python
# automatically puts the current working directory on the system path.
# In Jenkins, however, we have multiple copies of the edx-platform repo,
# each of which run "pip install -e ." (as part of requirements/edx/local.txt)
# Until we re-run pip install, the other copies of edx-platform could
# take precedence, leading to some very strange results.
sys.path.insert(0, os.path.dirname(__file__))

from pavelib import *
