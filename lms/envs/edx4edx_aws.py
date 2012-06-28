# Settings for edx4edx production instance
from .aws import *

COURSE_NAME = "edx4edx"
COURSE_NUMBER = "edX.01"
COURSE_TITLE = "edx4edx: edX Author Course"

PIPELINE_CSS_COMPRESSOR = None
PIPELINE_JS_COMPRESSOR = None
### Dark code. Should be enabled in local settings for devel. 
ENABLE_MULTICOURSE = True # set to False to disable multicourse display (see lib.util.views.mitxhome)
QUICKEDIT = True

###

COURSE_DEFAULT = 'edx4edx'
COURSE_SETTINGS =  {'edx4edx': {'number' : 'edX.01',
                                    'title'  : 'edx4edx: edX Author Course',
                                    'xmlpath': '/edx4edx/',
                                    'github_url': 'https://github.com/MITx/edx4edx',
                                    'active' : True,
                                    },
                    }
