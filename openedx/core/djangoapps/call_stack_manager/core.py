"""
Get call stacks of Model Class
in three cases-
1. QuerySet API
2. save()
3. delete()

classes:
CallStackManager -  stores all stacks in global dictionary and logs
CallStackMixin - used for Model save(), and delete() method

Functions:
capture_call_stack - global function used to store call stack

Decorators:
donottrack - mainly for the places where we know the calls. This decorator will let us not to track in specified cases

How to use-
1. Import following in the file where class to be tracked resides
    from openedx.core.djangoapps.call_stack_manager import CallStackManager, CallStackMixin
2. Override objects of default manager by writing following in any model class which you want to track-
    objects = CallStackManager()
3. For tracking Save and Delete events-
    Use mixin called "CallStackMixin"
    For ex.
        class StudentModule(CallStackMixin, models.Model):
4. Decorator is a parameterized decorator with class name/s as argument
    How to use -
    1. Import following
        import from openedx.core.djangoapps.call_stack_manager import donottrack
"""

import logging
import traceback
import re
import collections
from django.db.models import Manager

log = logging.getLogger(__name__)

# list of regular expressions acting as filters
REGULAR_EXPS = [re.compile(x) for x in ['^.*python2.7.*$', '^.*<exec_function>.*$', '^.*exec_code_object.*$',
                                        '^.*edxapp/src.*$', '^.*call_stack_manager.*$']]
# Variable which decides whether to track calls in the function or not. Do it by default.
TRACK_FLAG = True

# List keeping track of Model classes not be tracked for special cases
# usually cases where we know that the function is calling Model classes.
HALT_TRACKING = []

# Module Level variables
# dictionary which stores call stacks.
# { "ModelClasses" : [ListOfFrames]}
# Frames - ('FilePath','LineNumber','Context')
# ex. {"<class 'courseware.models.StudentModule'>" : [[(file,line number,context),(---,---,---)],
#                                                    [(file,line number,context),(---,---,---)]]}
STACK_BOOK = collections.defaultdict(list)


def capture_call_stack(current_model):
    """ logs customised call stacks in global dictionary `STACK_BOOK`, and logs it.

    Args:
        current_model - Name of the model class
    """
    # holds temporary callstack
    # frame[0][6:-1] -> File name along with path
    # frame[1][6:] -> Line Number
    # frame[2][3:] -> Context
    temp_call_stack = [(frame[0][6:-1],
                        frame[1][6:],
                        frame[2][3:])
                       for frame in [stack.replace("\n", "").strip().split(',') for stack in traceback.format_stack()]
                       if not any(reg.match(frame[0]) for reg in REGULAR_EXPS)]

    # avoid duplication.
    if temp_call_stack not in STACK_BOOK[current_model] and TRACK_FLAG \
            and not issubclass(current_model, tuple(HALT_TRACKING)):
        STACK_BOOK[current_model].append(temp_call_stack)
        log.info("logging new call stack for %s:\n %s", current_model, temp_call_stack)


class CallStackMixin(object):
    """ A mixin class for getting call stacks when Save() and Delete() methods are called
    """

    def save(self, *args, **kwargs):
        """
        Logs before save and overrides respective model API save()
        """
        capture_call_stack(type(self))
        return super(CallStackMixin, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """
        Logs before delete and overrides respective model API delete()
        """
        capture_call_stack(type(self))
        return super(CallStackMixin, self).delete(*args, **kwargs)


class CallStackManager(Manager):
    """ A Manager class which overrides the default Manager class for getting call stacks
    """
    def get_query_set(self):
        """overriding the default queryset API method
        """
        capture_call_stack(self.model)
        return super(CallStackManager, self).get_query_set()


def donottrack(*classes_not_to_be_tracked):
    """function decorator which deals with toggling call stack
    Args:
        classes_not_to_be_tracked: model classes where tracking is undesirable
    Returns:
        wrapped function
    """

    def real_donottrack(function):
        """takes function to be decorated and returns wrapped function

        Args:
            function - wrapped function i.e. real_donottrack
        """
        def wrapper(*args, **kwargs):
            """ wrapper function for decorated function
            Returns:
                wrapper function i.e. wrapper
            """
            if len(classes_not_to_be_tracked) == 0:
                global TRACK_FLAG  # pylint: disable=W0603
                current_flag = TRACK_FLAG
                TRACK_FLAG = False
                function(*args, **kwargs)
                TRACK_FLAG = current_flag
            else:
                global HALT_TRACKING  # pylint: disable=W0603
                current_halt_track = HALT_TRACKING
                HALT_TRACKING = classes_not_to_be_tracked
                function(*args, **kwargs)
                HALT_TRACKING = current_halt_track
        return wrapper
    return real_donottrack
