import hashlib
import json
import logging
import pyparsing
import sys

from django.conf import settings
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.http import Http404
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

from requests.auth import HTTPBasicAuth

from capa.xqueue_interface import XQueueInterface
from capa.chem import chemcalc
from courseware.access import has_access
from mitxmako.shortcuts import render_to_string
from models import StudentModule, StudentModuleCache
from psychometrics.psychoanalyze import make_psychometrics_data_update_handler
from static_replace import replace_urls
from xmodule.errortracker import exc_info_to_str
from xmodule.exceptions import NotFoundError
from xmodule.modulestore import Location
from xmodule.modulestore.django import modulestore
from xmodule.x_module import ModuleSystem
from xmodule.error_module import ErrorDescriptor, NonStaffErrorDescriptor
from xmodule.runtime import DbModel
from xmodule_modifiers import replace_course_urls, replace_static_urls, add_histogram, wrap_xmodule
from .model_data import LmsKeyValueStore, LmsUsage

from xmodule.modulestore.exceptions import ItemNotFoundError
from statsd import statsd

log = logging.getLogger("mitx.courseware")


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


def toc_for_course(user, request, course, active_chapter, active_section):
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
    '''

    student_module_cache = StudentModuleCache.cache_for_descriptor_descendents(
        course.id, user, course, depth=2)
    course_module = get_module(user, request, course.location, student_module_cache, course.id)
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
                sections.append({'display_name': section.lms.display_name,
                                 'url_name': section.url_name,
                                 'format': section.lms.format,
                                 'due': section.lms.due,
                                 'active': active,
                                 'graded': section.lms.graded,
                                 })

        chapters.append({'display_name': chapter.lms.display_name,
                         'url_name': chapter.url_name,
                         'sections': sections,
                         'active': chapter.url_name == active_chapter})
    return chapters


def get_module(user, request, location, student_module_cache, course_id, position=None, not_found_ok = False, wrap_xmodule_display = True):
    """
    Get an instance of the xmodule class identified by location,
    setting the state based on an existing StudentModule, or creating one if none
    exists.

    Arguments:
      - user                  : User for whom we're getting the module
      - request               : current django HTTPrequest.  Note: request.user isn't used for anything--all auth
                                and such works based on user.
      - location              : A Location-like object identifying the module to load
      - student_module_cache  : a StudentModuleCache
      - course_id             : the course_id in the context of which to load module
      - position              : extra information from URL for user-specified
                                position within module

    Returns: xmodule instance, or None if the user does not have access to the
    module.  If there's an error, will try to return an instance of ErrorModule
    if possible.  If not possible, return None.
    """
    try:
        return _get_module(user, request, location, student_module_cache, course_id, position, wrap_xmodule_display)
    except ItemNotFoundError:
        if not not_found_ok:
            log.exception("Error in get_module")
        return None
    except:
        # Something has gone terribly wrong, but still not letting it turn into a 500.
        log.exception("Error in get_module")
        return None


def _get_module(user, request, location, student_module_cache, course_id, position=None, wrap_xmodule_display=True):
    """
    Actually implement get_module.  See docstring there for details.
    """
    location = Location(location)
    descriptor = modulestore().get_instance(course_id, location)

    # Short circuit--if the user shouldn't have access, bail without doing any work
    if not has_access(user, descriptor, 'load', course_id):
        return None

    # Anonymized student identifier
    h = hashlib.md5()
    h.update(settings.SECRET_KEY)
    h.update(str(user.id))
    anonymous_student_id = h.hexdigest()

    # Setup system context for module instance
    ajax_url = reverse('modx_dispatch',
                       kwargs=dict(course_id=course_id,
                                   location=descriptor.location.url(),
                                   dispatch=''),
                       )
    # Intended use is as {ajax_url}/{dispatch_command}, so get rid of the trailing slash.
    ajax_url = ajax_url.rstrip('/')

    # Fully qualified callback URL for external queueing system
    xqueue_callback_url = '{proto}://{host}'.format(
        host=request.get_host(),
        proto=request.META.get('HTTP_X_FORWARDED_PROTO', 'https' if request.is_secure() else 'http')
    )
    xqueue_callback_url += reverse('xqueue_callback',
                                  kwargs=dict(course_id=course_id,
                                              userid=str(user.id),
                                              id=descriptor.location.url(),
                                              dispatch='score_update'),
                                  )

    # Default queuename is course-specific and is derived from the course that
    #   contains the current module.
    # TODO: Queuename should be derived from 'course_settings.json' of each course
    xqueue_default_queuename = descriptor.location.org + '-' + descriptor.location.course

    xqueue = {'interface': xqueue_interface,
              'callback_url': xqueue_callback_url,
              'default_queuename': xqueue_default_queuename.replace(' ', '_'),
              'waittime': settings.XQUEUE_WAITTIME_BETWEEN_REQUESTS
             }

    def inner_get_module(location):
        """
        Delegate to get_module.  It does an access check, so may return None
        """
        return get_module(user, request, location,
                                       student_module_cache, course_id, position)

    def xmodule_model_data(descriptor_model_data):
        return DbModel(
            LmsKeyValueStore(course_id, user, descriptor_model_data, student_module_cache),
            descriptor.module_class,
            user.id,
            LmsUsage(location, location)
        )

    def publish(event):
        if event.get('event_name') != 'grade':
            return

        student_module = student_module_cache.lookup(
            course_id, descriptor.location.category, descriptor.location.url()
        )
        if student_module is None:
            student_module = StudentModule(
                course_id=course_id,
                student=user,
                module_type=descriptor.location.category,
                module_state_key=descriptor.location.url(),
                state=json.dumps({})
            )
            student_module_cache.append(student_module)
        student_module.grade = event.get('value')
        student_module.max_grade = event.get('max_value')
        student_module.save()

    # TODO (cpennington): When modules are shared between courses, the static
    # prefix is going to have to be specific to the module, not the directory
    # that the xml was loaded from
    system = ModuleSystem(track_function=make_track_function(request),
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
                          replace_urls=replace_urls,
                          node_path=settings.NODE_PATH,
                          anonymous_student_id=anonymous_student_id,
                          xmodule_model_data=xmodule_model_data,
                          publish=publish,
                          )
    # pass position specified in URL to module through ModuleSystem
    system.set('position', position)
    system.set('DEBUG', settings.DEBUG)
    if settings.MITX_FEATURES.get('ENABLE_PSYCHOMETRICS') and instance_module is not None:
        system.set('psychometrics_handler',		# set callback for updating PsychometricsData
                   make_psychometrics_data_update_handler(instance_module))

    try:
        module = descriptor.xmodule(system)
    except:
        log.exception("Error creating module from descriptor {0}".format(descriptor))

        # make an ErrorDescriptor -- assuming that the descriptor's system is ok
        import_system = descriptor.system
        if has_access(user, location, 'staff', course_id):
            err_descriptor = ErrorDescriptor.from_xml(str(descriptor), import_system,
                                                      org=descriptor.location.org, course=descriptor.location.course,
                                                      error_msg=exc_info_to_str(sys.exc_info()))
        else:
            err_descriptor = NonStaffErrorDescriptor.from_xml(str(descriptor), import_system,
                                                              org=descriptor.location.org, course=descriptor.location.course,
                                                              error_msg=exc_info_to_str(sys.exc_info()))

        # Make an error module
        return err_descriptor.xmodule(system)

    _get_html = module.get_html

    if wrap_xmodule_display == True:
        _get_html = wrap_xmodule(module.get_html, module, 'xmodule_display.html')

    module.get_html = replace_static_urls(
        _get_html,
        getattr(module, 'data_dir', ''),
        course_namespace = module.location._replace(category=None, name=None))

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

    student_module_cache = StudentModuleCache.cache_for_descriptor_descendents(course_id,
        user, modulestore().get_instance(course_id, id), depth=0, select_for_update=True)
    instance = get_module(user, request, id, student_module_cache, course_id)
    if instance is None:
        log.debug("No module {0} for user {1}--access denied?".format(id, user))
        raise Http404

    instance_module = get_instance_module(course_id, user, instance, student_module_cache)

    if instance_module is None:
        log.debug("Couldn't find instance of module '%s' for user '%s'", id, user)
        raise Http404

    oldgrade = instance_module.grade
    old_instance_state = instance_module.state

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

    # Save state back to database
    instance_module.state = instance.get_instance_state()
    if instance.get_score():
        instance_module.grade = instance.get_score()['score']
    if instance_module.grade != oldgrade or instance_module.state != old_instance_state:
        instance_module.save()

        #Bin score into range and increment stats
        score_bucket=get_score_bucket(instance_module.grade, instance_module.max_grade)
        org, course_num, run=course_id.split("/")
        statsd.increment("lms.courseware.question_answered",
                        tags=["org:{0}".format(org),
                              "course:{0}".format(course_num),
                              "run:{0}".format(run),
                              "score_bucket:{0}".format(score_bucket),
                              "type:xqueue"])
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
    '''
    # ''' (fix emacs broken parsing)

    # Check parameters and fail fast if there's a problem
    if not Location.is_valid(location):
        raise Http404("Invalid location")

    # Check for submitted files and basic file size checks
    p = request.POST.copy()
    if request.FILES:
        for fileinput_id in request.FILES.keys():
            inputfiles = request.FILES.getlist(fileinput_id)

            if len(inputfiles) > settings.MAX_FILEUPLOADS_PER_INPUT:
                too_many_files_msg = 'Submission aborted! Maximum %d files may be submitted at once' %\
                    settings.MAX_FILEUPLOADS_PER_INPUT
                return HttpResponse(json.dumps({'success': too_many_files_msg}))

            for inputfile in inputfiles:
                if inputfile.size > settings.STUDENT_FILEUPLOAD_MAX_SIZE: # Bytes
                    file_too_big_msg = 'Submission aborted! Your file "%s" is too large (max size: %d MB)' %\
                                        (inputfile.name, settings.STUDENT_FILEUPLOAD_MAX_SIZE/(1000**2))
                    return HttpResponse(json.dumps({'success': file_too_big_msg}))
            p[fileinput_id] = inputfiles

    student_module_cache = StudentModuleCache.cache_for_descriptor_descendents(course_id,
        request.user, modulestore().get_instance(course_id, location))

    instance = get_module(request.user, request, location, student_module_cache, course_id)
    if instance is None:
        # Either permissions just changed, or someone is trying to be clever
        # and load something they shouldn't have access to.
        log.debug("No module {0} for user {1}--access denied?".format(location, request.user))
        raise Http404

    # Let the module handle the AJAX
    try:
        ajax_return = instance.handle_ajax(dispatch, p)
    except NotFoundError:
        log.exception("Module indicating to user that request doesn't exist")
        raise Http404
    except:
        log.exception("error processing ajax call")
        raise

    # Return whatever the module wanted to return to the client/caller
    return HttpResponse(ajax_return)

def preview_chemcalc(request):
    """
    Render an html preview of a chemical formula or equation.  The fact that
    this is here is a bit of hack.  See the note in lms/urls.py about why it's
    here. (Victor is to blame.)

    request should be a GET, with a key 'formula' and value 'some formula string'.

    Returns a json dictionary:
    {
       'preview' : 'the-preview-html' or ''
       'error' : 'the-error' or ''
    }
    """
    if request.method != "GET":
        raise Http404

    result = {'preview': '',
              'error': '' }
    formula = request.GET.get('formula')
    if formula is None:
        result['error'] = "No formula specified."

        return HttpResponse(json.dumps(result))

    try:
        result['preview'] = chemcalc.render_to_html(formula)
    except pyparsing.ParseException as p:
        result['error'] = "Couldn't parse formula: {0}".format(p)
    except Exception:
        # this is unexpected, so log
        log.warning("Error while previewing chemical formula", exc_info=True)
        result['error'] = "Error while rendering preview"

    return HttpResponse(json.dumps(result))


def get_score_bucket(grade,max_grade):
    """
    Function to split arbitrary score ranges into 3 buckets.
    Used with statsd tracking.
    """
    score_bucket="incorrect"
    if(grade>0 and grade<max_grade):
        score_bucket="partial"
    elif(grade==max_grade):
        score_bucket="correct"

    return score_bucket


