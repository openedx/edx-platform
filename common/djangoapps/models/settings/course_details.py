### A basic question is whether to break the details into schedule, intro, requirements, and misc sub objects
class CourseDetails:
    def __init__(self, location):
        self.course_location = location    # a Location obj
        self.start_date = None  # 'start'
        self.end_date = None    # 'end'
        self.enrollment_start = None
        self.enrollment_end = None
        self.syllabus = None    # a pdf file asset
        self.overview = ""      # html to render as the overview
        self.intro_video = None    # a video pointer
        self.effort = None      # int hours/week

    @classmethod
    def fetch(cls, course_location):
        """
        Fetch the course details for the given course from persistence and return a CourseDetails model.
        """
        course = cls(course_location)
        
        # TODO implement
        
        return course
        
