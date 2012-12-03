from xmodule.modulestore import Location
class CourseFaculty:
    def __init__(self, location):
        if not isinstance(location, Location):
            location = Location(location)
        # course_location is used so that updates know where to get the relevant data
        self.course_location = location
        self.first_name = ""
        self.last_name = ""
        self.photo = None
        self.bio = ""
        
        
    @classmethod
    def fetch(cls, course_location):
        """
        Fetch a list of faculty for the course
        """
        if not isinstance(course_location, Location):
            course_location = Location(course_location)
            
        # Must always have at least one faculty member (possibly empty)