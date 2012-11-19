from common.djangoapps.models.course_relative import CourseRelativeMember

### A basic question is whether to break the details into schedule, intro, requirements, and misc sub objects
class CourseDetails:
    def __init__(self, location):
        self.course_location = location    # a Location obj
        self.start_date = None
        self.end_date = None
        self.milestones = []
        self.syllabus = None    # a pdf file asset
        self.overview = ""      # html to render as the overview
        self.statement = ""
        self.intro_video = None    # a video pointer
        self.requirements = ""  # html
        self.effort = None      # int hours/week
        self.textbooks = []     # linked_asset
        self.prereqs = []       # linked_asset
        self.faqs = []          # summary_detail_pair

    @classmethod
    def fetch(cls, course_location):
        """
        Fetch the course details for the given course from persistence and return a CourseDetails model.
        """
        course = cls(course_location)
        
        # TODO implement
        
        return course
        
class CourseMilestone(CourseRelativeMember):
    def __init__(self, location, idx):
        CourseRelativeMember.__init__(self, location, idx)
        self.date = None
        self.description = ""

