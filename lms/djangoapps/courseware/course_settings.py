"""
Course settings module. All settings in the global_settings are
first applied, and then any settings in the settings.DATA_DIR/course_settings.json
are applied. A setting must be in ALL_CAPS. 
    
Settings are used by calling

from courseware.course_settings import course_settings

Note that courseware.course_settings.course_settings is not a module -- it's an object. So 
importing individual settings is not possible:

from courseware.course_settings.course_settings import GRADER  # This won't work.

"""
import json
import logging

from django.conf import settings

from xmodule import graders

log = logging.getLogger("mitx.courseware")

global_settings_json = """
{
	"GRADER" : [
	    {
	        "type" : "Homework",
	        "min_count" : 12,
	        "drop_count" : 2,
	        "short_label" : "HW",
	        "weight" : 0.15
	    },
	    {
	        "type" : "Lab",
	        "min_count" : 12,
	        "drop_count" : 2,
	        "category" : "Labs",
	        "weight" : 0.15
	    },
	    {
	        "type" : "Midterm",
	        "name" : "Midterm Exam",
	        "short_label" : "Midterm",
	        "weight" : 0.3
	    },
	    {
	        "type" : "Final",
	        "name" : "Final Exam",
	        "short_label" : "Final",
	        "weight" : 0.4
	    }
	],
	"GRADE_CUTOFFS" : {
		"A" : 0.87, 
		"B" : 0.7, 
		"C" : 0.6
	}
}
""" 


class Settings(object):
    def __init__(self):
        
        # Load the global settings as a dictionary
        global_settings = json.loads(global_settings_json)
        
        
        # Load the course settings as a dictionary
        course_settings = {}
        try:
            # TODO: this doesn't work with multicourse
            with open( settings.DATA_DIR + "/course_settings.json") as course_settings_file:
                course_settings_string = course_settings_file.read()
            course_settings = json.loads(course_settings_string)
        except IOError:
            log.warning("Unable to load course settings file from " + str(settings.DATA_DIR) + "/course_settings.json")
        
        
        # Override any global settings with the course settings
        global_settings.update(course_settings)
        
        # Now, set the properties from the course settings on ourselves
        for setting in global_settings:
            setting_value = global_settings[setting]
            setattr(self, setting, setting_value)
                
        # Here is where we should parse any configurations, so that we can fail early
        self.GRADER = graders.grader_from_conf(self.GRADER)

course_settings = Settings()
