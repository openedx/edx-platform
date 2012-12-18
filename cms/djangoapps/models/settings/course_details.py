from xmodule.modulestore.django import modulestore
from xmodule.modulestore import Location
from xmodule.modulestore.exceptions import ItemNotFoundError
import json
from json.encoder import JSONEncoder
import time
from contentstore.utils import get_modulestore
from util.converters import jsdate_to_time, time_to_date
from cms.djangoapps.models.settings import course_grading
from cms.djangoapps.contentstore.utils import update_item
import re


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
        
        descriptor = get_modulestore(course_location).get_item(course_location)
            
        course.start_date = descriptor.start
        course.end_date = descriptor.end
        course.enrollment_start = descriptor.enrollment_start
        course.enrollment_end = descriptor.enrollment_end
        
        temploc = course_location._replace(category='about', name='syllabus')
        try:
            course.syllabus = get_modulestore(temploc).get_item(temploc).definition['data']
        except ItemNotFoundError:
            pass

        temploc = temploc._replace(name='overview')
        try:
            course.overview = get_modulestore(temploc).get_item(temploc).definition['data']
        except ItemNotFoundError:
            pass
        
        temploc = temploc._replace(name='effort')
        try:
            course.effort = get_modulestore(temploc).get_item(temploc).definition['data']
        except ItemNotFoundError:
            pass
        
        temploc = temploc._replace(name='video')
        try:
            raw_video = get_modulestore(temploc).get_item(temploc).definition['data']
            course.intro_video = CourseDetails.parse_video_tag(raw_video) 
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
        descriptor = get_modulestore(course_location).get_item(course_location)
        
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
            get_modulestore(course_location).update_metadata(course_location, descriptor.metadata)
            
        # NOTE: below auto writes to the db w/o verifying that any of the fields actually changed
        # to make faster, could compare against db or could have client send over a list of which fields changed.
        temploc = Location(course_location)._replace(category='about', name='syllabus')
        update_item(temploc, jsondict['syllabus'])

        temploc = temploc._replace(name='overview')
        update_item(temploc, jsondict['overview'])
        
        temploc = temploc._replace(name='effort')
        update_item(temploc, jsondict['effort'])
        
        temploc = temploc._replace(name='video')
        recomposed_video_tag = CourseDetails.recompose_video_tag(jsondict['intro_video'])
        update_item(temploc, recomposed_video_tag)
        
                    
        # Could just generate and return a course obj w/o doing any db reads, but I put the reads in as a means to confirm
        # it persisted correctly
        return CourseDetails.fetch(course_location)
    
    @staticmethod
    def parse_video_tag(raw_video):
        """
        Because the client really only wants the author to specify the youtube key, that's all we send to and get from the client.
        The problem is that the db stores the html markup as well (which, of course, makes any sitewide changes to how we do videos
        next to impossible.)
        """
        if not raw_video:
            return None
         
        keystring_matcher = re.search('(?<=embed/)[a-zA-Z0-9_-]+', raw_video)
        if keystring_matcher is None:
            keystring_matcher = re.search('<?=\d+:[a-zA-Z0-9_-]+', raw_video)
        
        if keystring_matcher:
            return keystring_matcher.group(0)
        else:
            # TODO should this be None or the raw_video? It would be good to at least log this
            return None
    
    @staticmethod
    def recompose_video_tag(video_key):
        # TODO should this use a mako template? Of course, my hope is that this is a short-term workaround for the db not storing
        # the right thing
        result = '<iframe width="560" height="315" src="http://www.youtube.com/embed/' + \
            video_key + '?autoplay=1&rel=0" frameborder="0" allowfullscreen=""></iframe>'
        return result

    

# TODO move to a more general util? Is there a better way to do the isinstance model check?
class CourseSettingsEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, CourseDetails) or isinstance(obj, course_grading.CourseGradingModel):
            return obj.__dict__
        elif isinstance(obj, Location):
            return obj.dict()
        elif isinstance(obj, time.struct_time):
            return time_to_date(obj)
        else:
            return JSONEncoder.default(self, obj)
