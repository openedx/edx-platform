from xmodule.modulestore.django import modulestore
from xmodule.course_module import CourseDescriptor
from xmodule.modulestore import Location
from xmodule.modulestore.exceptions import ItemNotFoundError
import json
from json.encoder import JSONEncoder

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
        if not isinstance(course_location, Location):
            course_location = Location(course_location)
            
        course = cls(course_location)
        
        descriptor = modulestore('direct').get_item(course_location)
            
        ## DEBUG verify that this is a ClassDescriptor object
        if not isinstance(descriptor, CourseDescriptor):
            print("oops, not the expected type: ", descriptor)
        
        ## FIXME convert these from time.struct_time objects to something the client wants    
        course.start_date = descriptor.start
        course.end_date = descriptor.end
        course.enrollment_start = descriptor.enrollment_start
        course.enrollment_end = descriptor.enrollment_end
        
        temploc = course_location._replace(category='about', name='syllabus')
        try:
            course.syllabus = modulestore('direct').get_item(temploc).definition['data']
        except ItemNotFoundError:
            pass

        temploc = course_location._replace(name='overview')
        try:
            course.overview = modulestore('direct').get_item(temploc).definition['data']
        except ItemNotFoundError:
            pass
        
        temploc = course_location._replace(name='effort')
        try:
            course.effort = modulestore('direct').get_item(temploc).definition['data']
        except ItemNotFoundError:
            pass
        
        temploc = course_location._replace(name='video')
        try:
            course.intro_video = modulestore('direct').get_item(temploc).definition['data']
        except ItemNotFoundError:
            pass
        
        return course
        
    @classmethod
    def update_from_json(cls, jsonval):
        """
        Decode the json into CourseDetails and save any changed attrs to the db
        """
        jsondict = json.loads(jsonval)

        ## TODO make it an error for this to be undefined & for it to not be retrievable from modulestore        
        course_location = jsondict['course_location']
        ## Will probably want to cache the inflight courses because every blur generates an update
        descriptor = modulestore('direct').get_item(course_location)
        
        dirty = False
        
        ## FIXME do more accurate comparison (convert to time? or convert persisted from time)
        if (jsondict['start_date'] != descriptor.start):
            dirty = True
            descriptor.start = jsondict['start_date']
            
        if (jsondict['end_date'] != descriptor.start):
            dirty = True
            descriptor.end = jsondict['end_date']
            
        if (jsondict['enrollment_start'] != descriptor.enrollment_start):
            dirty = True
            descriptor.enrollment_start = jsondict['enrollment_start']
            
        if (jsondict['enrollment_end'] != descriptor.enrollment_end):
            dirty = True
            descriptor.enrollment_end = jsondict['enrollment_end']
            
        if dirty:
            modulestore('direct').update_item(course_location, descriptor.definition['data'])
            
        # NOTE: below auto writes to the db w/o verifying that any of the fields actually changed
        # to make faster, could compare against db or could have client send over a list of which fields changed.
        temploc = course_location._replace(category='about', name='syllabus')
        modulestore('direct').update_item(temploc, jsondict['syllabus'])

        temploc = course_location._replace(name='overview')
        modulestore('direct').update_item(temploc, jsondict['overview'])
        
        temploc = course_location._replace(name='effort')
        modulestore('direct').update_item(temploc, jsondict['effort'])
        
        temploc = course_location._replace(name='video')
        modulestore('direct').update_item(temploc, jsondict['intro_video'])
        
                    
        # Could just generate and return a course obj w/o doing any db reads, but I put the reads in as a means to confirm
        # it persisted correctly
        return CourseDetails.fetch(course_location)
    
class CourseDetailsEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, CourseDetails):
            return obj.__dict__
        elif isinstance(obj, Location):
            return obj.dict()
        else:
            return JSONEncoder.default(self, obj)