"""
Call Stack Manager deals with tracking call stacks of functions/methods/classes(Django Model Classes)
Call Stack Manager logs unique call stacks. The call stacks then can be retrieved via Splunk, or log reads.

classes:
CallStackManager -  stores all stacks in global dictionary and logs
CallStackMixin - used for Model save(), and delete() method

Decorators:
@donottrack - Decorator that will halt tracking for parameterized entities,
 (or halt tracking anything in case of non-parametrized decorator).
@trackit - Decorator that will start tracking decorated entity.
@track_till_now - Will log every unique call stack of parametrized entity/ entities.

TRACKING DJANGO MODEL CLASSES -
Call stacks of Model Class
in three cases-
1. QuerySet API
2. save()
3. delete()

How to use:
1. Import following in the file where class to be tracked resides
    from openedx.core.djangoapps.call_stack_manager import CallStackManager, CallStackMixin
2. Override objects of default manager by writing following in any model class which you want to track-
    objects = CallStackManager()
3. For tracking Save and Delete events-
    Use mixin called "CallStackMixin"
    For ex.
        class StudentModule(models.Model, CallStackMixin):

TRACKING FUNCTIONS, and METHODS-
1. Import following-
    from openedx.core.djangoapps.call_stack_manager import trackit
NOTE - @trackit is non-parameterized decorator.

FOR DISABLING TRACKING-
1. Import following at appropriate location-
    from openedx.core.djangoapps.call_stack_manager import donottrack
NOTE - You need to import function/class you do not want to track.
"""

import logging
import traceback
import re
import collections
import wrapt
import types
import inspect
from django.db.models import Manager

log = logging.getLogger(__name__)

# List of regular expressions acting as filters
REGULAR_EXPS = [re.compile(x) for x in ['^.*python2.7.*$', '^.*<exec_function>.*$', '^.*exec_code_object.*$',
                                        '^.*edxapp/src.*$', '^.*call_stack_manager.*$']]

# List keeping track of entities not to be tracked
HALT_TRACKING = []

STACK_BOOK = collections.defaultdict(list)
# Dictionary which stores call logs
# {'EntityName' : ListOf<CallStacks>}
# CallStacks is ListOf<Frame>
# Frame is a tuple ('FilePath','LineNumber','Function Name', 'Context')
# {"<class 'courseware.models.StudentModule'>" : [[(file, line number, function name, context),(---,---,---)],
#                                                 [(file, line number, function name, context),(---,---,---)]]}


def capture_call_stack(entity_name):
    """ Logs customised call stacks in global dictionary STACK_BOOK and logs it.

    Arguments:
        entity_name - entity
    """
    # Holds temporary callstack
    # List with each element 4-tuple(filename, line number, function name, text)
    # and filtered with respect to regular expressions
    temp_call_stack = [frame for frame in traceback.extract_stack()
                       if not any(reg.match(frame[0]) for reg in REGULAR_EXPS)]

    final_call_stack = "".join(traceback.format_list(temp_call_stack))

    def _should_get_logged(entity_name):  # pylint: disable=
        """ Checks if current call stack of current entity should be logged or not.

        Arguments:
            entity_name - Name of the current entity
        Returns:
            True if the current call stack is to logged, False otherwise
        """
        is_class_in_halt_tracking = bool(HALT_TRACKING and inspect.isclass(entity_name) and
                                         issubclass(entity_name, tuple(HALT_TRACKING[-1])))

        is_function_in_halt_tracking = bool(HALT_TRACKING and not inspect.isclass(entity_name) and
                                            any((entity_name.__name__ == x.__name__ and
                                                 entity_name.__module__ == x.__module__)
                                                for x in tuple(HALT_TRACKING[-1])))

        is_top_none = HALT_TRACKING and HALT_TRACKING[-1] is None
        # if top of STACK_BOOK is None
        if is_top_none:
            return False
        # if call stack is empty
        if not temp_call_stack:
            return False

        if HALT_TRACKING:
            if is_class_in_halt_tracking or is_function_in_halt_tracking:
                return False
            else:
                return temp_call_stack not in STACK_BOOK[entity_name]
        else:
            return temp_call_stack not in STACK_BOOK[entity_name]

    if _should_get_logged(entity_name):
        STACK_BOOK[entity_name].append(temp_call_stack)
        if inspect.isclass(entity_name):
            log.info("Logging new call stack number %s for %s:\n %s", len(STACK_BOOK[entity_name]),
                     entity_name, final_call_stack)
        else:
            log.info("Logging new call stack number %s for %s.%s:\n %s", len(STACK_BOOK[entity_name]),
                     entity_name.__module__, entity_name.__name__, final_call_stack)


class CallStackMixin(object):
    """ Mixin class for getting call stacks when save() and delete() methods are called """
    def save(self, *args, **kwargs):
        """ Logs before save() and overrides respective model API save() """
        capture_call_stack(type(self))
        return super(CallStackMixin, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """ Logs before delete() and overrides respective model API delete() """
        capture_call_stack(type(self))
        return super(CallStackMixin, self).delete(*args, **kwargs)


class CallStackManager(Manager):
    """ Manager class which overrides the default Manager class for getting call stacks """
    def get_queryset(self):
        """ Override the default queryset API method """
        capture_call_stack(self.model)
        return super(CallStackManager, self).get_queryset()


def donottrack(*entities_not_to_be_tracked):
    """ Decorator which halts tracking for some entities for specific functions

    Arguments:
        entities_not_to_be_tracked: entities which are not to be tracked

    Returns:
        wrapped function
    """
    if not entities_not_to_be_tracked:
        entities_not_to_be_tracked = None

    @wrapt.decorator
    def real_donottrack(wrapped, instance, args, kwargs):  # pylint: disable=unused-argument
        """ Takes function to be decorated and returns wrapped function

        Arguments:
            wrapped - The wrapped function which in turns needs to be called by wrapper function
            instance - The object to which the wrapped function was bound when it was called.
            args - The list of positional arguments supplied when the decorated function was called.
            kwargs - The dictionary of keyword arguments supplied when the decorated function was called.

        Returns:
            return of wrapped function
        """
        global HALT_TRACKING  # pylint: disable=global-variable-not-assigned
        if entities_not_to_be_tracked is None:
            HALT_TRACKING.append(None)
        else:
            if HALT_TRACKING:
                if HALT_TRACKING[-1] is None:  # if @donottrack() calls @donottrack('xyz')
                    pass
                else:
                    HALT_TRACKING.append(set(HALT_TRACKING[-1].union(set(entities_not_to_be_tracked))))
            else:
                HALT_TRACKING.append(set(entities_not_to_be_tracked))

        return_value = wrapped(*args, **kwargs)
        # check if the returning class is a generator
        if isinstance(return_value, types.GeneratorType):
            def generator_wrapper(wrapped_generator):
                """ Function handling wrapped yielding values.

                Argument:
                    wrapped_generator - wrapped function returning generator function

                Returns:
                    Generator Wrapper
                """
                try:
                    while True:
                        return_value = next(wrapped_generator)
                        yield return_value
                finally:
                    if HALT_TRACKING:
                        HALT_TRACKING.pop()
            return generator_wrapper(return_value)
        else:
            if HALT_TRACKING:
                HALT_TRACKING.pop()
            return return_value
    return real_donottrack


@wrapt.decorator
def trackit(wrapped, instance, args, kwargs):  # pylint: disable=unused-argument
    """ Decorator which tracks logs call stacks

    Arguments:
        wrapped - The wrapped function which in turns needs to be called by wrapper function.
        instance - The object to which the wrapped function was bound when it was called.
        args - The list of positional arguments supplied when the decorated function was called.
        kwargs - The dictionary of keyword arguments supplied when the decorated function was called.

    Returns:
        wrapped function
    """
    capture_call_stack(wrapped)
    return wrapped(*args, **kwargs)
