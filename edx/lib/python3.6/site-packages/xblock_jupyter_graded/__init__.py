from .xblock_jupyter_graded import JupyterGradedXBlock
import os
from config import EDX_ROOT

default_app_config = 'xblock_jupyter_graded.apps.JupyterGradedXBlock'

# TODO: Is this the right place to do this? Maybe during setup.py somewhere?
if not os.path.exists(EDX_ROOT):
    os.makedirs(EDX_ROOT)


