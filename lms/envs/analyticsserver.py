"""

This config file is used to host an analytics server. The edX codebase
is fairly monolithic, and expensive to import from within the
analytics framework. It also mixes up Django authentication databases,
etc. The analytics framework is fairly modular, and easy to import
from within edX. With this configuration, we can import analytics as a
library into the core edX platform, and use it to expose data through
the standard analytics protocols. The main analytics servers can then
use this to pull data out.

This should configuration should never be enabled on a production LMS. 

This configuration should also never be used as the main analytics
server. It should only be used as a thin layer to allow access to edX
data in a way that can use the edX libraries. When used in this mode,
it should only be granted access to read replicas of the databases. 

"""
# import json

ROOT_URLCONF = 'lms.urls'

# import sys

from .common import *
from .dev import *
from logsettings import get_logger_config

MITX_FEATURES['RUN_AS_ANALYTICS_SERVER_ENABLED'] = True

INSTALLED_APPS = INSTALLED_APPS + ( 'djeventstream.httphandler',
    'djcelery',
    'south',
    'edinsights.core',
    'edinsights.modulefs',
)

INSTALLED_ANALYTICS_MODULES = open("../analytics_modules.txt").readlines()
INSTALLED_ANALYTICS_MODULES = [x.strip() for x in INSTALLED_ANALYTICS_MODULES if x and len(x)>1]

print "======JUHO==========", INSTALLED_ANALYTICS_MODULES

DJFS = { 'type' : 'osfs',
         'directory_root' : '/tmp/djfsmodule',
         'url_root' : 'file:///tmp/'
       }

import djcelery

djcelery.setup_loader()
default_optional_kwargs = ['fs','db','query']
