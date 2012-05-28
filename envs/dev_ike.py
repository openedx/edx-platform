"""
This config file runs the simplest dev environment using sqlite, and db-based
sessions. Assumes structure:

/envroot/
        /db   # This is where it'll write the database file
        /mitx # The location of this repo
        /log  # Where we're going to write log files
"""
from envs.common import *
from envs.logsettings import get_logger_config
from dev import *

#-----------------------------------------------------------------------------
# ichuang

DEBUG = True
ENABLE_MULTICOURSE = True     # set to False to disable multicourse display (see lib.util.views.mitxhome)
QUICKEDIT = True
MITX_ROOT_URL = ''

COURSE_SETTINGS =  {'6.002_Spring_2012': {'number' : '6.002x',
                                          'title'  :  'Circuits and Electronics',
                                          'xmlpath': '/6002x/',
                                          'active' : True,
                                          },
                    '8.02_Spring_2013': {'number' : '8.02x',
                                         'title'  : 'Electricity &amp; Magnetism',
                                         'xmlpath': '/802x/',
                                          'active' : True,
                                         },
                    '8.01_Spring_2013': {'number' : '8.01x',
                                         'title'  : 'Mechanics',
                                         'xmlpath': '/801x/',
                                         'active' : False,
                                         },
                    '6.189_Spring_2013': {'number' : '6.189x',
                                         'title'  : 'IAP Python Programming',
                                         'xmlpath': '/6189-pytutor/',
                                          'active' : True,
                                         },
                    '8.01_Summer_2012': {'number' : '8.01x',
                                         'title'  : 'Mechanics',
                                         'xmlpath': '/801x-summer/',
                                         'active': True,
                                         },
                    'edx4edx': {'number' : 'edX.01',
                                    'title'  : 'edx4edx: edX Author Course',
                                    'xmlpath': '/edx4edx/',
                                    'active' : True,
                                    },
                    }

#-----------------------------------------------------------------------------

