"""
Course settings module. The settings are based of django.conf. All settings in
courseware.global_course_settings are first applied, and then any settings
in the settings.DATA_DIR/course_settings.py are applied. A setting must be
in ALL_CAPS.
    
Settings are used by calling
    
from courseware import course_settings

Note that courseware.course_settings is not a module -- it's an object. So 
importing individual settings is not possible:

from courseware.course_settings import GRADER  # This won't work.

"""

import courseware
import imp
import logging
import sys
import types

from django.conf import settings
from django.utils.functional import SimpleLazyObject
from courseware import global_course_settings

_log = logging.getLogger("mitx.courseware")

class Settings(object):
    def __init__(self):
        # update this dict from global settings (but only for ALL_CAPS settings)
        for setting in dir(global_course_settings):
            if setting == setting.upper():
                setattr(self, setting, getattr(global_course_settings, setting))
                
        fp = None
        try:
            fp, pathname, description = imp.find_module("course_settings", [settings.DATA_DIR])
            mod = imp.load_module("course_settings", fp, pathname, description)
        except Exception as e:
            _log.error("Unable to import course settings file from " + settings.DATA_DIR + ". Error: " + str(e))
            mod = types.ModuleType('course_settings')
        finally:
            if fp:
                fp.close()
                
        for setting in dir(mod):
            if setting == setting.upper():
                setting_value = getattr(mod, setting)
                setattr(self, setting, setting_value)

course_settings = Settings()