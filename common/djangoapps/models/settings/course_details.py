from xmodule.modulestore.django import modulestore
from xmodule.modulestore import Location
from xmodule.modulestore.exceptions import ItemNotFoundError
import json
from json.encoder import JSONEncoder
import time
from util.converters import jsdate_to_time, time_to_date

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
            
        course.start_date = descriptor.start
        course.end_date = descriptor.end
        course.enrollment_start = descriptor.enrollment_start
        course.enrollment_end = descriptor.enrollment_end
        
        temploc = course_location._replace(category='about', name='syllabus')
        try:
            course.syllabus = modulestore('direct').get_item(temploc).definition['data']
        except ItemNotFoundError:
            pass

        temploc = temploc._replace(name='overview')
        try:
            course.overview = modulestore('direct').get_item(temploc).definition['data']
        except ItemNotFoundError:
            pass
        
        temploc = temploc._replace(name='effort')
        try:
            course.effort = modulestore('direct').get_item(temploc).definition['data']
        except ItemNotFoundError:
            pass
        
        temploc = temploc._replace(name='video')
        try:
            course.intro_video = modulestore('direct').get_item(temploc).definition['data']
        except ItemNotFoundError:
            pass
        
        return course
        
    @classmethod
    def update_from_json(cls, jsondict):
        """
        Decode the json into CourseDetails and save any changed attrs to the db
        """
        ## TODO make it an error for this to be undefined & for it to not be retrievable from modulestore        
        course_location = jsondict['course_location']
        ## Will probably want to cache the inflight courses because every blur generates an update
        descriptor = modulestore('direct').get_item(course_location)
        
        dirty = False
        
        ## ??? Will this comparison work?
        if 'start_date' in jsondict:
            converted = jsdate_to_time(jsondict['start_date'])
        else:
            converted = None
        if converted != descriptor.start:
            dirty = True
            descriptor.start = converted
            
        if 'end_date' in jsondict:
            converted = jsdate_to_time(jsondict['end_date'])
        else:
            converted = None

        if converted != descriptor.end:
            dirty = True
            descriptor.end = converted
            
        if 'enrollment_start' in jsondict:
            converted = jsdate_to_time(jsondict['enrollment_start'])
        else:
            converted = None

        if converted != descriptor.enrollment_start:
            dirty = True
            descriptor.enrollment_start = converted
            
        if 'enrollment_end' in jsondict:
            converted = jsdate_to_time(jsondict['enrollment_end'])
        else:
            converted = None

        if converted != descriptor.enrollment_end:
            dirty = True
            descriptor.enrollment_end = converted
            
        if dirty:
            modulestore('direct').update_metadata(course_location, descriptor.metadata)
            
        # NOTE: below auto writes to the db w/o verifying that any of the fields actually changed
        # to make faster, could compare against db or could have client send over a list of which fields changed.
        temploc = Location(course_location)._replace(category='about', name='syllabus')
        modulestore('direct').update_item(temploc, jsondict['syllabus'])

        temploc = temploc._replace(name='overview')
        modulestore('direct').update_item(temploc, jsondict['overview'])
        
        temploc = temploc._replace(name='effort')
        modulestore('direct').update_item(temploc, jsondict['effort'])
        
        temploc = temploc._replace(name='video')
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
        elif isinstance(obj, time.struct_time):
            return time_to_date(obj)
        else:
            return JSONEncoder.default(self, obj)
