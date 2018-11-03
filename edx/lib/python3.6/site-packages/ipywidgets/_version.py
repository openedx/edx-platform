# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

version_info = (7, 4, 2, 'final', 0)

_specifier_ = {'alpha': 'a', 'beta': 'b', 'candidate': 'rc', 'final': ''}

__version__ = '%s.%s.%s%s'%(version_info[0], version_info[1], version_info[2],
  '' if version_info[3]=='final' else _specifier_[version_info[3]]+str(version_info[4]))

__protocol_version__ = '2.0.0'
__jupyter_widgets_base_version__ = '1.1.0'
__jupyter_widgets_output_version__ = '1.0.0'
__jupyter_widgets_controls_version__ = '1.4.0'

# A compatible @jupyter-widgets/html-manager npm package semver range
__html_manager_version__ = '^0.14.0'
