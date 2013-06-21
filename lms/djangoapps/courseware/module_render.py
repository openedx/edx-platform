import json
import logging
import re
import sys
import static_replace

from functools import partial

from django.conf import settings
from django.contrib.auth.models import User
from django.core.cache import cache
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.http import Http404
from django.http import HttpResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt

from requests.auth import HTTPBasicAuth

from capa.xqueue_interface import XQueueInterface
from courseware.masquerade import setup_masquerade
from courseware.access import has_access
from mitxmako.shortcuts import render_to_string
from .models import StudentModule
from psychometrics.psychoanalyze import make_psychometrics_data_update_handler
from student.models import unique_id_for_user
from xmodule.errortracker import exc_info_to_str
from xmodule.exceptions import NotFoundError, ProcessingError
from xmodule.modulestore import Location
from xmodule.modulestore.django import modulestore
from xmodule.x_module import ModuleSystem
from xmodule.error_module import ErrorDescriptor, NonStaffErrorDescriptor
from xblock.runtime import DbModel
from xmodule_modifiers import replace_course_urls, replace_static_urls, add_histogram, wrap_xmodule
from .model_data import LmsKeyValueStore, LmsUsage, ModelDataCache

from xmodule.modulestore.exceptions import ItemNotFoundError
from statsd import statsd

log = logging.getLogger(__name__)


if settings.XQUEUE_INTERFACE.get('basic_auth') is not None:
    requests_auth = HTTPBasicAuth(*settings.XQUEUE_INTERFACE['basic_auth'])
else:
    requests_auth = None

xqueue_interface = XQueueInterface(
    settings.XQUEUE_INTERFACE['url'],
    settings.XQUEUE_INTERFACE['django_auth'],
    requests_auth,
)


def make_track_function(request):
    '''
    Make a tracking function that logs what happened.
    For use in ModuleSystem.
    '''
    import track.views

    def f(event_type, event):
        return track.views.server_track(request, event_type, event, page='x_module')
    return f


def toc_for_course(user, request, course, active_chapter, active_section, model_data_cache):
    '''
    Create a table of contents from the module store

    Return format:
    [ {'display_name': name, 'url_name': url_name,
       'sections': SECTIONS, 'active': bool}, ... ]

    where SECTIONS is a list
    [ {'display_name': name, 'url_name': url_name,
       'format': format, 'due': due, 'active' : bool, 'graded': bool}, ...]

    active is set for the section and chapter corresponding to the passed
    parameters, which are expected to be url_names of the chapter+section.
    Everything else comes from the xml, or defaults to "".

    chapters with name 'hidden' are skipped.

    NOTE: assumes that if we got this far, user has access to course.  Returns
    None if this is not the case.

    model_data_cache must include data from the course module and 2 levels of its descendents
    '''

    course_module = get_module_for_descriptor(user, request, course, model_data_cache, course.id)
    if course_module is None:
        return None

    chapters = list()
    for chapter in course_module.get_display_items():
        if chapter.lms.hide_from_toc:
            continue

        sections = list()
        for section in chapter.get_display_items():

            active = (chapter.url_name == active_chapter and
                      section.url_name == active_section)

            if not section.lms.hide_from_toc:
                sections.append({'display_name': section.display_name_with_default,
                                 'url_name': section.url_name,
                                 'format': section.lms.format if section.lms.format is not None else '',
                                 'due': section.lms.due,
                                 'active': active,
                                 'graded': section.lms.graded,
                                 })

        chapters.append({'display_name': chapter.display_name_with_default,
                         'url_name': chapter.url_name,
                         'sections': sections,
                         'active': chapter.url_name == active_chapter})
    return chapters


def get_module(user, request, location, model_data_cache, course_id,
               position=None, not_found_ok=False, wrap_xmodule_display=True,
               grade_bucket_type=None, depth=0):
    """
    Get an instance of the xmodule class identified by location,
    setting the state based on an existing StudentModule, or creating one if none
    exists.

    Arguments:
      - user                  : User for whom we're getting the module
      - request               : current django HTTPrequest.  Note: request.user isn't used for anything--all auth
                                and such works based on user.
      - location              : A Location-like object identifying the module to load
      - model_data_cache      : a ModelDataCache
      - course_id             : the course_id in the context of which to load module
      - position              : extra information from URL for user-specified
                                position within module
      - depth                 : number of levels of descendents to cache when loading this module.
                                None means cache all descendents

    Returns: xmodule instance, or None if the user does not have access to the
    module.  If there's an error, will try to return an instance of ErrorModule
    if possible.  If not possible, return None.
    """
    try:
        location = Location(location)
        descriptor = modulestore().get_instance(course_id, location, depth=depth)
        return get_module_for_descriptor(user, request, descriptor, model_data_cache, course_id,
                                         position=position,
                                         wrap_xmodule_display=wrap_xmodule_display,
                                         grade_bucket_type=grade_bucket_type)
    except ItemNotFoundError:
        if not not_found_ok:
            log.exception("Error in get_module")
        return None
    except:
        # Something has gone terribly wrong, but still not letting it turn into a 500.
        log.exception("Error in get_module")
        return None


def get_xqueue_callback_url_prefix(request):
    """
    Calculates default prefix based on request, but allows override via settings

    This is separated from get_module_for_descriptor so that it can be called
    by the LMS before submitting background tasks to run.  The xqueue callbacks
    should go back to the LMS, not to the worker.
    """
    prefix = '{proto}://{host}'.format(
            proto=request.META.get('HTTP_X_FORWARDED_PROTO', 'https' if request.is_secure() else 'http'),
            host=request.get_host()
        )
    return settings.XQUEUE_INTERFACE.get('callback_url', prefix)


def get_module_for_descriptor(user, request, descriptor, model_data_cache, course_id,
                              position=None, wrap_xmodule_display=True, grade_bucket_type=None):
    """
    Implements get_module, extracting out the request-specific functionality.

    See get_module() docstring for further details.
    """
    # allow course staff to masquerade as student
    if has_access(user, descriptor, 'staff', course_id):
        setup_masquerade(request, True)

    track_function = make_track_function(request)
    xqueue_callback_url_prefix = get_xqueue_callback_url_prefix(request)

    return get_module_for_descriptor_internal(user, descriptor, model_data_cache, course_id,
                                              track_function, xqueue_callback_url_prefix,
                                              position, wrap_xmodule_display, grade_bucket_type)


def get_module_for_descriptor_internal(user, descriptor, model_data_cache, course_id,
                                       track_function, xqueue_callback_url_prefix,
                                       position=None, wrap_xmodule_display=True, grade_bucket_type=None):
    """
    Actually implement get_module, without requiring a request.

    See get_module() docstring for further details.
    """

    # Short circuit--if the user shouldn't have access, bail without doing any work
    if not has_access(user, descriptor, 'load', course_id):
        return None

    # Setup system context for module instance
    ajax_url = reverse('modx_dispatch',
                       kwargs=dict(course_id=course_id,
                                   location=descriptor.location.url(),
                                   dispatch=''),
                       )
    # Intended use is as {ajax_url}/{dispatch_command}, so get rid of the trailing slash.
    ajax_url = ajax_url.rstrip('/')

    def make_xqueue_callback(dispatch='score_update'):
        # Fully qualified callback URL for external queueing system
        relative_xqueue_callback_url = reverse('xqueue_callback',
                                               kwargs=dict(course_id=course_id,
                                                           userid=str(user.id),
                                                           id=descriptor.location.url(),
                                                           dispatch=dispatch),
                                       )
        return xqueue_callback_url_prefix + relative_xqueue_callback_url

    # Default queuename is course-specific and is derived from the course that
    #   contains the current module.
    # TODO: Queuename should be derived from 'course_settings.json' of each course
    xqueue_default_queuename = descriptor.location.org + '-' + descriptor.location.course

    xqueue = {'interface': xqueue_interface,
              'construct_callback': make_xqueue_callback,
              'default_queuename': xqueue_default_queuename.replace(' ', '_'),
              'waittime': settings.XQUEUE_WAITTIME_BETWEEN_REQUESTS
             }

    # This is a hacky way to pass settings to the combined open ended xmodule
    # It needs an S3 interface to upload images to S3
    # It needs the open ended grading interface in order to get peer grading to be done
    # this first checks to see if the descriptor is the correct one, and only sends settings if it is

    # Get descriptor metadata fields indicating needs for various settings
    needs_open_ended_interface = getattr(descriptor, "needs_open_ended_interface", False)
    needs_s3_interface = getattr(descriptor, "needs_s3_interface", False)

    # Initialize interfaces to None
    open_ended_grading_interface = None
    s3_interface = None

    # Create interfaces if needed
    if needs_open_ended_interface:
        open_ended_grading_interface = settings.OPEN_ENDED_GRADING_INTERFACE
        open_ended_grading_interface['mock_peer_grading'] = settings.MOCK_PEER_GRADING
        open_ended_grading_interface['mock_staff_grading'] = settings.MOCK_STAFF_GRADING
    if needs_s3_interface:
        s3_interface = {
            'access_key': getattr(settings, 'AWS_ACCESS_KEY_ID', ''),
            'secret_access_key': getattr(settings, 'AWS_SECRET_ACCESS_KEY', ''),
            'storage_bucket_name': getattr(settings, 'AWS_STORAGE_BUCKET_NAME', 'openended')
        }

    def inner_get_module(descriptor):
        """
        Delegate to get_module_for_descriptor_internal() with all values except `descriptor` set.

        Because it does an access check, it may return None.
        """
        # TODO: fix this so that make_xqueue_callback uses the descriptor passed into
        # inner_get_module, not the parent's callback.  Add it as an argument....
        return get_module_for_descriptor_internal(user, descriptor, model_data_cache, course_id,
                                                  track_function, make_xqueue_callback,
                                                  position, wrap_xmodule_display, grade_bucket_type)

    def xblock_model_data(descriptor):
        return DbModel(
            LmsKeyValueStore(descriptor._model_data, model_data_cache),
            descriptor.module_class,
            user.id,
            LmsUsage(descriptor.location, descriptor.location)
        )

    def publish(event):
        if event.get('event_name') != 'grade':
            return

        student_module, created = StudentModule.objects.get_or_create(
            course_id=course_id,
            student=user,
            module_type=descriptor.location.category,
            module_state_key=descriptor.location.url(),
            defaults={'state': '{}'},
        )
        student_module.grade = event.get('value')
        student_module.max_grade = event.get('max_value')
        student_module.save()

        # Bin score into range and increment stats
        score_bucket = get_score_bucket(student_module.grade, student_module.max_grade)
        org, course_num, run = course_id.split("/")

        tags = ["org:{0}".format(org),
                "course:{0}".format(course_num),
                "run:{0}".format(run),
                "score_bucket:{0}".format(score_bucket)]

        if grade_bucket_type is not None:
            tags.append('type:%s' % grade_bucket_type)

        statsd.increment("lms.courseware.question_answered", tags=tags)

    def can_execute_unsafe_code():
        # To decide if we can run unsafe code, we check the course id against
        # a list of regexes configured on the server.
        for regex in settings.COURSES_WITH_UNSAFE_CODE:
            if re.match(regex, course_id):
                return True
        return False

    # TODO (cpennington): When modules are shared between courses, the static
    # prefix is going to have to be specific to the module, not the directory
    # that the xml was loaded from
    system = ModuleSystem(track_function=track_function,
                          render_template=render_to_string,
                          ajax_url=ajax_url,
                          xqueue=xqueue,
                          # TODO (cpennington): Figure out how to share info between systems
                          filestore=descriptor.system.resources_fs,
                          get_module=inner_get_module,
                          user=user,
                          # TODO (cpennington): This should be removed when all html from
                          # a module is coming through get_html and is therefore covered
                          # by the replace_static_urls code below
                          replace_urls=partial(
                              static_replace.replace_static_urls,
                              data_directory=getattr(descriptor, 'data_dir', None),
                              course_namespace=descriptor.location._replace(category=None, name=None),
                          ),
                          node_path=settings.NODE_PATH,
                          xblock_model_data=xblock_model_data,
                          publish=publish,
                          anonymous_student_id=unique_id_for_user(user),
                          course_id=course_id,
                          open_ended_grading_interface=open_ended_grading_interface,
                          s3_interface=s3_interface,
                          cache=cache,
                          can_execute_unsafe_code=can_execute_unsafe_code,
                          )
    # pass position specified in URL to module through ModuleSystem
    system.set('position', position)
    system.set('DEBUG', settings.DEBUG)
    if settings.MITX_FEATURES.get('ENABLE_PSYCHOMETRICS'):
        system.set('psychometrics_handler',		# set callback for updating PsychometricsData
                   make_psychometrics_data_update_handler(course_id, user, descriptor.location.url()))

    try:
        module = descriptor.xmodule(system)
    except:
        log.exception("Error creating module from descriptor {0}".format(descriptor))

        # make an ErrorDescriptor -- assuming that the descriptor's system is ok
        if has_access(user, descriptor.location, 'staff', course_id):
            err_descriptor_class = ErrorDescriptor
        else:
            err_descriptor_class = NonStaffErrorDescriptor

        err_descriptor = err_descriptor_class.from_descriptor(
            descriptor,
            error_msg=exc_info_to_str(sys.exc_info())
        )

        # Make an error module
        return err_descriptor.xmodule(system)

    system.set('user_is_staff', has_access(user, descriptor.location, 'staff', course_id))
    _get_html = module.get_html

    if wrap_xmodule_display == True:
        _get_html = wrap_xmodule(module.get_html, module, 'xmodule_display.html')

    module.get_html = replace_static_urls(
        _get_html,
        getattr(descriptor, 'data_dir', None),
        course_namespace=module.location._replace(category=None, name=None))

    # Allow URLs of the form '/course/' refer to the root of multicourse directory
    #   hierarchy of this course
    module.get_html = replace_course_urls(module.get_html, course_id)

    if settings.MITX_FEATURES.get('DISPLAY_HISTOGRAMS_TO_STAFF'):
        if has_access(user, module, 'staff', course_id):
            module.get_html = add_histogram(module.get_html, module, user)

    return module


@csrf_exempt
def xqueue_callback(request, course_id, userid, id, dispatch):
    '''
    Entry point for graded results from the queueing system.
    '''
    # Test xqueue package, which we expect to be:
    #   xpackage = {'xqueue_header': json.dumps({'lms_key':'secretkey',...}),
    #               'xqueue_body'  : 'Message from grader'}
    get = request.POST.copy()
    for key in ['xqueue_header', 'xqueue_body']:
        if not get.has_key(key):
            raise Http404
    header = json.loads(get['xqueue_header'])
    if not isinstance(header, dict) or not header.has_key('lms_key'):
        raise Http404

    # Retrieve target StudentModule
    user = User.objects.get(id=userid)

    model_data_cache = ModelDataCache.cache_for_descriptor_descendents(course_id,
        user, modulestore().get_instance(course_id, id), depth=0, select_for_update=True)
    instance = get_module(user, request, id, model_data_cache, course_id, grade_bucket_type='xqueue')
    if instance is None:
        log.debug("No module {0} for user {1}--access denied?".format(id, user))
        raise Http404

    # Transfer 'queuekey' from xqueue response header to 'get'. This is required to
    #   use the interface defined by 'handle_ajax'
    get.update({'queuekey': header['lms_key']})

    # We go through the "AJAX" path
    #   So far, the only dispatch from xqueue will be 'score_update'
    try:
        # Can ignore the return value--not used for xqueue_callback
        instance.handle_ajax(dispatch, get)
    except:
        log.exception("error processing ajax call")
        raise

    return HttpResponse("")


def modx_dispatch(request, dispatch, location, course_id):
    ''' Generic view for extensions. This is where AJAX calls go.

    Arguments:

      - request -- the django request.
      - dispatch -- the command string to pass through to the module's handle_ajax call
           (e.g. 'problem_reset').  If this string contains '?', only pass
           through the part before the first '?'.
      - location -- the module location. Used to look up the XModule instance
      - course_id -- defines the course context for this request.

    Raises PermissionDenied if the user is not logged in. Raises Http404 if
    the location and course_id do not identify a valid module, the module is
    not accessible by the user, or the module raises NotFoundError. If the
    module raises any other error, it will escape this function.
    '''
    # ''' (fix emacs broken parsing)

    # Check parameters and fail fast if there's a problem
    if not Location.is_valid(location):
        raise Http404("Invalid location")

    if not request.user.is_authenticated():
        raise PermissionDenied

    # Check for submitted files and basic file size checks
    p = request.POST.copy()
    if request.FILES:
        for fileinput_id in request.FILES.keys():
            inputfiles = request.FILES.getlist(fileinput_id)

            if len(inputfiles) > settings.MAX_FILEUPLOADS_PER_INPUT:
                too_many_files_msg = 'Submission aborted! Maximum %d files may be submitted at once' % \
                    settings.MAX_FILEUPLOADS_PER_INPUT
                return HttpResponse(json.dumps({'success': too_many_files_msg}))

            for inputfile in inputfiles:
                if inputfile.size > settings.STUDENT_FILEUPLOAD_MAX_SIZE:  # Bytes
                    file_too_big_msg = 'Submission aborted! Your file "%s" is too large (max size: %d MB)' % \
                                        (inputfile.name, settings.STUDENT_FILEUPLOAD_MAX_SIZE / (1000 ** 2))
                    return HttpResponse(json.dumps({'success': file_too_big_msg}))
            p[fileinput_id] = inputfiles

    try:
        descriptor = modulestore().get_instance(course_id, location)
    except ItemNotFoundError:
        log.warn(
            "Invalid location for course id {course_id}: {location}".format(
                course_id=course_id,
                location=location
            )
        )
        raise Http404

    model_data_cache = ModelDataCache.cache_for_descriptor_descendents(course_id,
        request.user, descriptor)

    instance = get_module(request.user, request, location, model_data_cache, course_id, grade_bucket_type='ajax')
    if instance is None:
        # Either permissions just changed, or someone is trying to be clever
        # and load something they shouldn't have access to.
        log.debug("No module {0} for user {1}--access denied?".format(location, request.user))
        raise Http404

    # Let the module handle the AJAX
    try:
        ajax_return = instance.handle_ajax(dispatch, p)

    # If we can't find the module, respond with a 404
    except NotFoundError:
        log.exception("Module indicating to user that request doesn't exist")
        raise Http404

    # For XModule-specific errors, we respond with 400
    except ProcessingError:
        log.warning("Module encountered an error while prcessing AJAX call",
                    exc_info=True)
        return HttpResponseBadRequest()

    # If any other error occurred, re-raise it to trigger a 500 response
    except:
        log.exception("error processing ajax call")
        raise

    # Return whatever the module wanted to return to the client/caller
    return HttpResponse(ajax_return)



def get_score_bucket(grade, max_grade):
    """
    Function to split arbitrary score ranges into 3 buckets.
    Used with statsd tracking.
    """
    score_bucket = "incorrect"
    if(grade > 0 and grade < max_grade):
        score_bucket = "partial"
    elif(grade == max_grade):
        score_bucket = "correct"

    return score_bucket
