# Source: django-simplewiki. GPL license.

import os
import sys

# allow mdx_* parsers to be just dropped in the simplewiki folder
module_path = os.path.abspath(os.path.dirname(__file__))
if module_path not in sys.path:
    sys.path.append(module_path)
