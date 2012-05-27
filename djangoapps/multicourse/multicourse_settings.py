# multicourse/multicourse_settings.py
#
# central module for providing fixed settings (course name, number, title)
# for multiple courses.  Loads this information from django.conf.settings
#
# Allows backward compatibility with settings configurations without
# multiple courses specified.
#
# The central piece of configuration data is the dict COURSE_SETTINGS, with
# keys being the COURSE_NAME (spaces ok), and the value being a dict of
# parameter,value pairs. The required parameters are:
#
# - number  : course number (used in the simplewiki pages)
# - title   : humanized descriptive course title
#
# Optional parameters:
#
# - xmlpath : path (relative to data directory) for this course (defaults to "")
#
# If COURSE_SETTINGS does not exist, then fallback to 6.002_Spring_2012 default,
# for now.

from django.conf import settings

#-----------------------------------------------------------------------------
# load course settings

if hasattr(settings,'COURSE_SETTINGS'):    	# in the future, this could be replaced by reading an XML file
    COURSE_SETTINGS = settings.COURSE_SETTINGS

elif hasattr(settings,'COURSE_NAME'):		# backward compatibility
    COURSE_SETTINGS = {settings.COURSE_NAME: {'number': settings.COURSE_NUMBER,
                                              'title':  settings.COURSE_TITLE,
                                              },
                       }
else:						# default to 6.002_Spring_2012
    COURSE_SETTINGS = {'6.002_Spring_2012': {'number': '6.002x',
                                              'title':  'Circuits and Electronics',
                                              },
                       }

#-----------------------------------------------------------------------------
# wrapper functions around course settings

def get_coursename_from_request(request):
    if 'coursename' in request.session:
        coursename = request.session['coursename']
        settings.COURSE_TITLE = get_course_title(coursename) 	# overwrite settings.COURSE_TITLE based on this
    else: coursename = None
    return coursename

def get_course_settings(coursename):
    if not coursename:
        if hasattr(settings,'COURSE_DEFAULT'):
            coursename = settings.COURSE_DEFAULT
        else:
            coursename = '6.002_Spring_2012'
    if coursename in COURSE_SETTINGS: return COURSE_SETTINGS[coursename]
    coursename = coursename.replace(' ','_')
    if coursename in COURSE_SETTINGS: return COURSE_SETTINGS[coursename]
    return None

def is_valid_course(coursename):
    return not (get_course_settings==None)

def get_course_property(coursename,property):
    cs = get_course_settings(coursename)
    if not cs: return ''	# raise exception instead?
    if property in cs: return cs[property]
    return ''	# default

def get_course_xmlpath(coursename):
    return get_course_property(coursename,'xmlpath')

def get_course_title(coursename):
    return get_course_property(coursename,'title')

def get_course_number(coursename):
    return get_course_property(coursename,'number')
    
def is_dogfood(coursename):
    return True if get_course_property(coursename,'is_dogfood') else False

