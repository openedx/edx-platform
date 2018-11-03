""" For beta/alpha/rc releases, the version number for a beta is X.Y.ZbN
**without dots between the last 'micro' number and b**. N is the number of
the beta released i.e. 1, 2, 3 ...

See PEP 440 https://www.python.org/dev/peps/pep-0440/
"""

version_info = (6, 0, 0)

__version__ = '.'.join(map(str, version_info[:3])) + ''.join(version_info[3:])
