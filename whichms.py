from opaque_keys.edx.keys import CourseKey
from xmodule.modulestore.django import modulestore

course_key = CourseKey.from_string("edX/MODULESTORE_100/2018")
m = modulestore()
course = m.get_course(course_key)
print course

