'''
common xblock modules
'''

# Appends this package to the xblock namespace first defined by github.com/edx/XBlock.git
# This change quiets the pylint warnings, e,g,
# * No name 'core' in module 'xblock' (no-name-in-module)
# * Unable to import 'xblock.core' (import-error)
from pkgutil import extend_path
__path__ = extend_path(__path__, __name__)
