import os
from os.path import join as pjoin
import six
from six.moves import configparser


# If running in Google App Engine there is no "user" and
# os.path.expanduser() will fail. Attempt to detect this case and use a
# no-op expanduser function in this case.
try:
  os.path.expanduser('~')
  expanduser = os.path.expanduser
except (AttributeError, ImportError):
  # This is probably running on App Engine.
  expanduser = (lambda x: x)

# By default we use two locations for the doto configurations,
# /etc/Doto.cfg and ~/.doto (which works on Windows and Unix).
DotoConfigPath = '/etc/dotorc.cfg'
DotoConfigLocations = [DotoConfigPath]
UserConfigPath = pjoin(expanduser('~'),'.doto', '.dotorc')
DotoConfigLocations.append(UserConfigPath)

# If there's a DOTO_CONFIG variable set, we load ONLY
# that variable
if 'DOTO_CONFIG' in os.environ:
    DotoConfigLocations = [expanduser(os.environ['DOTO_CONFIG'])]

# If there's a DOTO_PATH variable set, we use anything there
# as the current configuration locations, split with colons
elif 'DOTO_PATH' in os.environ:
    DotoConfigLocations = []
    for path in os.environ['DOTO_PATH'].split(":"):
        DotoConfigLocations.append(expanduser(path))

class Config(configparser.SafeConfigParser):

    def __init__(self, path=None,):
        if six.PY3:
            super(Config,self).__init__(allow_no_value=True)
        else:
            # We don't use ``super`` here, because ``ConfigParser`` still uses
            # old-style classes.
            configparser.SafeConfigParser.__init__(self, allow_no_value=True)

        if path:
            self.read(path)
            self.file_path = path
        else:
            f = self.read(DotoConfigLocations)
            self.file_path = f[0]

    def get(self, section, name, default=None):
        try:
            val = configparser.SafeConfigParser.get(self, section, name)
        except:
            val = default
        return val
