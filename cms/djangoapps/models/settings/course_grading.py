from xmodule.modulestore import Location
from contentstore.utils import get_modulestore
import datetime
import re
from common.djangoapps.util import converters
import time


class CourseGradingModel:
    """
    Basically a DAO and Model combo for CRUD operations pertaining to grading policy. 
    """
    def __init__(self, course_descriptor):
        self.course_location = course_descriptor.location
        self.graders = [CourseGradingModel.jsonize_grader(i, grader) for i, grader in enumerate(course_descriptor.raw_grader)] # weights transformed to ints [0..100]
        self.grade_cutoffs = course_descriptor.grade_cutoffs
        self.grace_period = CourseGradingModel.convert_set_grace_period(course_descriptor)
        
    @classmethod    
    def fetch(cls, course_location):
        """
        Fetch the course details for the given course from persistence and return a CourseDetails model.
        """
        if not isinstance(course_location, Location):
            course_location = Location(course_location)
        
        descriptor = get_modulestore(course_location).get_item(course_location)

        model = cls(descriptor)
        return model
    
    @staticmethod
    def fetch_grader(course_location, index):
        """
        Fetch the course's nth grader  
        Returns an empty dict if there's no such grader.
        """
        if not isinstance(course_location, Location):
            course_location = Location(course_location)
        
        descriptor = get_modulestore(course_location).get_item(course_location)
        # # ??? it would be good if these had the course_location in them so that they stand alone sufficiently
        # # but that would require not using CourseDescriptor's field directly. Opinions?
        
        # FIXME how do I tell it to ignore index? Is there another iteration mech I should use?
        if len(descriptor.raw_grader) > index: 
            return CourseGradingModel.jsonize_grader(index, descriptor.raw_grader[index])
            
        # return empty model
        else:
            return {
                    "id" : index,
                    "type" : "",
                    "min_count" : 0,
                    "drop_count" : 0,
                    "short_label" : None,
                    "weight" : 0
                }
    
    @staticmethod
    def fetch_cutoffs(course_location):
        """
        Fetch the course's grade cutoffs.
        """
        if not isinstance(course_location, Location):
            course_location = Location(course_location)
        
        descriptor = get_modulestore(course_location).get_item(course_location)
        return descriptor.grade_cutoffs

    @staticmethod
    def fetch_grace_period(course_location):
        """
        Fetch the course's default grace period.
        """
        if not isinstance(course_location, Location):
            course_location = Location(course_location)
        
        descriptor = get_modulestore(course_location).get_item(course_location)
        return {'grace_period' : CourseGradingModel.convert_set_grace_period(descriptor) }
        
    @staticmethod
    def update_from_json(jsondict):
        """
        Decode the json into CourseGradingModel and save any changes. Returns the modified model.
        Probably not the usual path for updates as it's too coarse grained.
        """
        course_location = jsondict['course_location']
        descriptor = get_modulestore(course_location).get_item(course_location)
        
        graders_parsed = [CourseGradingModel.parse_grader(jsonele) for jsonele in jsondict['graders']]
        
        descriptor.raw_grader = graders_parsed
        descriptor.grade_cutoffs = jsondict['grade_cutoffs']
        
        get_modulestore(course_location).update_item(course_location, descriptor.definition['data'])
        CourseGradingModel.update_grace_period_from_json(course_location, jsondict['grace_period'])
        
        return CourseGradingModel.fetch(course_location)
          
        
    @staticmethod
    def update_grader_from_json(course_location, grader):
        """
        Create or update the grader of the given type (string key) for the given course. Returns the modified 
        grader which is a full model on the client but not on the server (just a dict)
        """
        if not isinstance(course_location, Location):
            course_location = Location(course_location)
        
        descriptor = get_modulestore(course_location).get_item(course_location)
        # # ??? it would be good if these had the course_location in them so that they stand alone sufficiently
        # # but that would require not using CourseDescriptor's field directly. Opinions?

        # parse removes the id; so, grab it before parse        
        index = grader.get('id', None)
        grader = CourseGradingModel.parse_grader(grader)

        if index < len(descriptor.raw_grader):
            descriptor.raw_grader[index] = grader
        else:
            descriptor.raw_grader.append(grader)
            
        get_modulestore(course_location).update_item(course_location, descriptor.definition['data'])
        
        return CourseGradingModel.jsonize_grader(index, descriptor.raw_grader[index])
        
    @staticmethod
    def update_cutoffs_from_json(course_location, cutoffs):
        """
        Create or update the grade cutoffs for the given course. Returns sent in cutoffs (ie., no extra
        db fetch).
        """
        if not isinstance(course_location, Location):
            course_location = Location(course_location)
        
        descriptor = get_modulestore(course_location).get_item(course_location)
        descriptor.grade_cutoffs = cutoffs
        get_modulestore(course_location).update_item(course_location, descriptor.definition['data'])
        
        return cutoffs
        
        
    @staticmethod
    def update_grace_period_from_json(course_location, graceperiodjson):
        """
        Update the course's default grace period.
        """
        if not isinstance(course_location, Location):
            course_location = Location(course_location)
            
        if not isinstance(graceperiodjson, dict):
            graceperiodjson = {'grace_period' : graceperiodjson}
        
        grace_time = converters.jsdate_to_time(graceperiodjson['grace_period'])
        # NOTE: this does not handle > 24 hours
        grace_rep = time.strftime("%H hours %M minutes %S seconds", grace_time)
        
        descriptor = get_modulestore(course_location).get_item(course_location)
        descriptor.metadata['graceperiod'] = grace_rep  
        get_modulestore(course_location).update_metadata(course_location, descriptor.metadata)
        
        return graceperiodjson
        
        
    @staticmethod
    def delete_grader(course_location, index):
        """
        Delete the grader of the given type from the given course.
        """
        if not isinstance(course_location, Location):
            course_location = Location(course_location)
        
        descriptor = get_modulestore(course_location).get_item(course_location)
        if index < len(descriptor.raw_grader):
            del descriptor.raw_grader[index]
            get_modulestore(course_location).update_item(course_location, descriptor.definition['data'])
        
    # NOTE cannot delete cutoffs. May be useful to reset 
    @staticmethod
    def delete_cutoffs(course_location, cutoffs):
        """
        Resets the cutoffs to the defaults
        """
        if not isinstance(course_location, Location):
            course_location = Location(course_location)
        
        descriptor = get_modulestore(course_location).get_item(course_location)
        descriptor.grade_cutoffs = descriptor.defaut_grading_policy['GRADE_CUTOFFS']
        get_modulestore(course_location).update_item(course_location, descriptor.definition['data'])
        
        return descriptor.grade_cutoffs
        
    @staticmethod
    def delete_grace_period(course_location):
        """
        Delete the course's default grace period.
        """
        if not isinstance(course_location, Location):
            course_location = Location(course_location)
            
        descriptor = get_modulestore(course_location).get_item(course_location)
        del descriptor.metadata['graceperiod']   
        get_modulestore(course_location).update_metadata(course_location, descriptor.metadata)
        
    @staticmethod
    def convert_set_grace_period(descriptor):
        # 5 hours 59 minutes 59 seconds => converted to iso format
        rawgrace = descriptor.metadata.get('graceperiod', None)
        if rawgrace:
            parsedgrace = {str(key): val for (val, key) in re.findall('\s*(\d*)\s*(\w*)', rawgrace)}
            gracedate = datetime.datetime.today()
            gracedate = gracedate.replace(minute = int(parsedgrace.get('minutes',0)), hour = int(parsedgrace.get('hours',0))) 
            return gracedate.isoformat() + 'Z'
        else: return None

    @staticmethod
    def parse_grader(json_grader):
        # manual to clear out kruft
        result = {
                    "type" : json_grader["type"],
                    "min_count" : int(json_grader.get('min_count', 0)),
                    "drop_count" : int(json_grader.get('drop_count', 0)),
                    "short_label" : json_grader.get('short_label', None),
                    "weight" : float(json_grader.get('weight', 0)) / 100.0
                }
            
        return result

    @staticmethod
    def jsonize_grader(i, grader):
        grader['id'] = i
        if grader['weight']:
            grader['weight'] *= 100
        if not 'short_label' in grader:
            grader['short_label'] = ""  
              
        return grader