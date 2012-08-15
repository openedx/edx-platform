import json
import logging

from django.conf import settings
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.http import Http404
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

from requests.auth import HTTPBasicAuth

from capa.xqueue_interface import XQueueInterface
from courseware.access import has_access
from mitxmako.shortcuts import render_to_string
from models import StudentModule, StudentModuleCache
from static_replace import replace_urls
from xmodule.exceptions import NotFoundError
from xmodule.modulestore import Location
from xmodule.modulestore.django import modulestore
from xmodule.x_module import ModuleSystem
from xmodule_modifiers import replace_static_urls, add_histogram, wrap_xmodule

log = logging.getLogger("mitx.courseware")


if settings.XQUEUE_INTERFACE['basic_auth'] is not None:
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
       'format': format, 'due': due, 'active' : bool}, ...]

    active is set for the section and chapter corresponding to the passed
    parameters, which are expected to be url_names of the chapter+section.
    Everything else comes from the xml, or defaults to "".

    chapters with name 'hidden' are skipped.

    NOTE: assumes that if we got this far, user has access to course.  Returns
    None if this is not the case.
    '''

    student_module_cache = StudentModuleCache.cache_for_descriptor_descendents(user, course, depth=2)
    course = get_module(user, request, course.location, student_module_cache)

    chapters = list()
    for chapter in course.get_display_items():
        sections = list()
        for section in chapter.get_display_items():

            active = (chapter.url_name == active_chapter and
                      section.url_name == active_section)
            hide_from_toc = section.metadata.get('hide_from_toc', 'false').lower() == 'true'

            if not hide_from_toc:
                sections.append({'display_name': section.display_name,
                                 'url_name': section.url_name,
                                 'format': section.metadata.get('format', ''),
                                 'due': section.metadata.get('due', ''),
                                 'active': active})

        chapters.append({'display_name': chapter.display_name,
                         'url_name': chapter.url_name,
                         'sections': sections,
                         'active': chapter.url_name == active_chapter})
    return chapters


def get_section(course_module, chapter, section):
    """
    Returns the xmodule descriptor for the name course > chapter > section,
    or None if this doesn't specify a valid section

    course: Course url
    chapter: Chapter url_name
    section: Section url_name
    """

    if course_module is None:
        return

    chapter_module = None
    for _chapter in course_module.get_children():
        if _chapter.url_name == chapter:
            chapter_module = _chapter
            break

    if chapter_module is None:
        return

    section_module = None
    for _section in chapter_module.get_children():
        if _section.url_name == section:
            section_module = _section
            break

    return section_module


def get_module(user, request, location, student_module_cache, position=None):
    ''' Get an instance of the xmodule class identified by location,
    setting the state based on an existing StudentModule, or creating one if none
    exists.

    Arguments:
      - user                  : current django User
      - request               : current django HTTPrequest
      - location              : A Location-like object identifying the module to load
      - student_module_cache  : a StudentModuleCache
      - position              : extra information from URL for user-specified
                                position within module

    Returns: xmodule instance

    '''
    descriptor = modulestore().get_item(location)

    # Short circuit--if the user shouldn't have access, bail without doing any work
    if not has_access(user, descriptor, 'load'):
        return None

    #TODO Only check the cache if this module can possibly have state
    instance_module = None
    shared_module = None
    if user.is_authenticated():
        if descriptor.stores_state:
            instance_module = student_module_cache.lookup(descriptor.category,
                                                  descriptor.location.url())

        shared_state_key = getattr(descriptor, 'shared_state_key', None)
        if shared_state_key is not None:
            shared_module = student_module_cache.lookup(descriptor.category,
                                                        shared_state_key)

    instance_state = instance_module.state if instance_module is not None else None
    shared_state = shared_module.state if shared_module is not None else None

    # Setup system context for module instance
    ajax_url = reverse('modx_dispatch',
                       kwargs=dict(course_id=descriptor.location.course_id,
                                   id=descriptor.location.url(),
                                   dispatch=''),
                       )

    # Fully qualified callback URL for external queueing system
    xqueue_callback_url  = request.build_absolute_uri('/')[:-1] # Trailing slash provided by reverse
    xqueue_callback_url += reverse('xqueue_callback',
                                  kwargs=dict(course_id=descriptor.location.course_id,
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
              'default_queuename': xqueue_default_queuename.replace(' ', '_')}

    def _get_module(location):
        """
        Delegate to get_module.  It does an access check, so may return None
        """
        return get_module(user, request, location,
                                       student_module_cache, position)

    # TODO (cpennington): When modules are shared between courses, the static
    # prefix is going to have to be specific to the module, not the directory
    # that the xml was loaded from
    system = ModuleSystem(track_function=make_track_function(request),
                          render_template=render_to_string,
                          ajax_url=ajax_url,
                          xqueue=xqueue,
                          # TODO (cpennington): Figure out how to share info between systems
                          filestore=descriptor.system.resources_fs,
                          get_module=_get_module,
                          user=user,
                          # TODO (cpennington): This should be removed when all html from
                          # a module is coming through get_html and is therefore covered
                          # by the replace_static_urls code below
                          replace_urls=replace_urls,
                          node_path=settings.NODE_PATH
                          )
    # pass position specified in URL to module through ModuleSystem
    system.set('position', position)
    system.set('DEBUG', settings.DEBUG)

    module = descriptor.xmodule_constructor(system)(instance_state, shared_state)

    module.get_html = replace_static_urls(
        wrap_xmodule(module.get_html, module, 'xmodule_display.html'),
        module.metadata['data_dir'], module
    )

    if settings.MITX_FEATURES.get('DISPLAY_HISTOGRAMS_TO_STAFF'):
        if has_access(user, module, 'staff'):
            module.get_html = add_histogram(module.get_html, module, user)

    return module

def get_instance_module(user, module, student_module_cache):
    """
    Returns instance_module is a StudentModule specific to this module for this student,
        or None if this is an anonymous user
    """
    if user.is_authenticated():
        if not module.descriptor.stores_state:
            log.exception("Attempted to get the instance_module for a module "
                          + str(module.id) + " which does not store state.")
            return None

        instance_module = student_module_cache.lookup(module.category,
                                              module.location.url())

        if not instance_module:
            instance_module = StudentModule(
                student=user,
                module_type=module.category,
                module_state_key=module.id,
                state=module.get_instance_state(),
                max_grade=module.max_score())
            instance_module.save()
            student_module_cache.append(instance_module)

        return instance_module
    else:
        return None

def get_shared_instance_module(user, module, student_module_cache):
    """
    Return shared_module is a StudentModule specific to all modules with the same
        'shared_state_key' attribute, or None if the module does not elect to
        share state
    """
    if user.is_authenticated():
        # To get the shared_state_key, we need to descriptor
        descriptor = modulestore().get_item(module.location)

        shared_state_key = getattr(module, 'shared_state_key', None)
        if shared_state_key is not None:
            shared_module = student_module_cache.lookup(module.category,
                                                        shared_state_key)
            if not shared_module:
                shared_module = StudentModule(
                    student=user,
                    module_type=descriptor.category,
                    module_state_key=shared_state_key,
                    state=module.get_shared_state())
                shared_module.save()
                student_module_cache.append(shared_module)
        else:
            shared_module = None

        return shared_module
    else:
        return None

@csrf_exempt
def xqueue_callback(request, course_id, userid, id, dispatch):
    '''
    Entry point for graded results from the queueing system.
    '''
    # Test xqueue package, which we expect to be:
    #   xpackage = {'xqueue_header': json.dumps({'lms_key':'secretkey',...}),
    #               'xqueue_body'  : 'Message from grader}
    get = request.POST.copy()
    for key in ['xqueue_header', 'xqueue_body']:
        if not get.has_key(key):
            return Http404
    header = json.loads(get['xqueue_header'])
    if not isinstance(header, dict) or not header.has_key('lms_key'):
        return Http404

    # Retrieve target StudentModule
    user = User.objects.get(id=userid)

    student_module_cache = StudentModuleCache.cache_for_descriptor_descendents(user, modulestore().get_item(id))
    instance = get_module(user, request, id, student_module_cache)
    if instance is None:
        log.debug("No module {} for user {}--access denied?".format(id, user))
        raise Http404

    instance_module = get_instance_module(user, instance, student_module_cache)

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
        ajax_return = instance.handle_ajax(dispatch, get)  # Can ignore the "ajax" return in 'xqueue_callback'
    except:
        log.exception("error processing ajax call")
        raise

    # Save state back to database
    instance_module.state = instance.get_instance_state()
    if instance.get_score():
        instance_module.grade = instance.get_score()['score']
    if instance_module.grade != oldgrade or instance_module.state != old_instance_state:
        instance_module.save()

    return HttpResponse("")


def modx_dispatch(request, dispatch=None, id=None, course_id=None):
    ''' Generic view for extensions. This is where AJAX calls go.

    Arguments:

      - request -- the django request.
      - dispatch -- the command string to pass through to the module's handle_ajax call
           (e.g. 'problem_reset').  If this string contains '?', only pass
           through the part before the first '?'.
      - id -- the module id. Used to look up the XModule instance
    '''
    # ''' (fix emacs broken parsing)

    # Check for submitted files and basic file size checks
    p = request.POST.copy()
    if request.FILES:
        for inputfile_id in request.FILES.keys():
            inputfile = request.FILES[inputfile_id]
            if inputfile.size > settings.STUDENT_FILEUPLOAD_MAX_SIZE: # Bytes
                file_too_big_msg = 'Submission aborted! Your file "%s" is too large (max size: %d MB)' %\
                                    (inputfile.name, settings.STUDENT_FILEUPLOAD_MAX_SIZE/(1000**2))
                return HttpResponse(json.dumps({'success': file_too_big_msg}))
            p[inputfile_id] = inputfile

    student_module_cache = StudentModuleCache.cache_for_descriptor_descendents(request.user, modulestore().get_item(id))
    instance = get_module(request.user, request, id, student_module_cache)
    if instance is None:
        # Either permissions just changed, or someone is trying to be clever
        # and load something they shouldn't have access to.
        log.debug("No module {} for user {}--access denied?".format(id, user))
        raise Http404

    instance_module = get_instance_module(request.user, instance, student_module_cache)
    shared_module = get_shared_instance_module(request.user, instance, student_module_cache)

    # Don't track state for anonymous users (who don't have student modules)
    if instance_module is not None:
        oldgrade = instance_module.grade
        old_instance_state = instance_module.state
        old_shared_state = shared_module.state if shared_module is not None else None

    # Let the module handle the AJAX
    try:
        ajax_return = instance.handle_ajax(dispatch, p)
    except NotFoundError:
        log.exception("Module indicating to user that request doesn't exist")
        raise Http404
    except:
        log.exception("error processing ajax call")
        raise

    # Save the state back to the database
    # Don't track state for anonymous users (who don't have student modules)
    if instance_module is not None:
        instance_module.state = instance.get_instance_state()
        if instance.get_score():
            instance_module.grade = instance.get_score()['score']
        if instance_module.grade != oldgrade or instance_module.state != old_instance_state:
            instance_module.save()

    if shared_module is not None:
        shared_module.state = instance.get_shared_state()
        if shared_module.state != old_shared_state:
            shared_module.save()

    # Return whatever the module wanted to return to the client/caller
    return HttpResponse(ajax_return)
