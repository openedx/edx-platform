import json
import logging

from django.conf import settings
from django.http import Http404
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

from django.contrib.auth.models import User
from xmodule.modulestore.django import modulestore
from mitxmako.shortcuts import render_to_string
from models import StudentModule, StudentModuleCache
from static_replace import replace_urls
from xmodule.exceptions import NotFoundError
from xmodule.x_module import ModuleSystem
from xmodule_modifiers import replace_static_urls, add_histogram, wrap_xmodule

log = logging.getLogger("mitx.courseware")


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
    [ {'name': name, 'sections': SECTIONS, 'active': bool}, ... ]

    where SECTIONS is a list
    [ {'name': name, 'format': format, 'due': due, 'active' : bool}, ...]

    active is set for the section and chapter corresponding to the passed
    parameters.  Everything else comes from the xml, or defaults to "".

    chapters with name 'hidden' are skipped.
    '''

    student_module_cache = StudentModuleCache(user, course, depth=2)
    (course, _, _, _) = get_module(user, request, course.location, student_module_cache)

    chapters = list()
    for chapter in course.get_display_items():
        sections = list()
        for section in chapter.get_display_items():

            active = (chapter.metadata.get('display_name') == active_chapter and
                      section.metadata.get('display_name') == active_section)
            hide_from_toc = section.metadata.get('hide_from_toc', 'false').lower() == 'true'

            if not hide_from_toc:
                sections.append({'name': section.metadata.get('display_name'),
                                 'format': section.metadata.get('format', ''),
                                 'due': section.metadata.get('due', ''),
                                 'active': active})

        chapters.append({'name': chapter.metadata.get('display_name'),
                         'sections': sections,
                         'active': chapter.metadata.get('display_name') == active_chapter})
    return chapters


def get_section(course_module, chapter, section):
    """
    Returns the xmodule descriptor for the name course > chapter > section,
    or None if this doesn't specify a valid section

    course: Course url
    chapter: Chapter name
    section: Section name
    """

    if course_module is None:
        return

    chapter_module = None
    for _chapter in course_module.get_children():
        if _chapter.metadata.get('display_name') == chapter:
            chapter_module = _chapter
            break

    if chapter_module is None:
        return

    section_module = None
    for _section in chapter_module.get_children():
        if _section.metadata.get('display_name') == section:
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

    Returns:
      - a tuple (xmodule instance, instance_module, shared_module, module category).
        instance_module is a StudentModule specific to this module for this student,
            or None if this is an anonymous user
        shared_module is a StudentModule specific to all modules with the same
            'shared_state_key' attribute, or None if the module does not elect to
            share state
    '''
    descriptor = modulestore().get_item(location)

    instance_module = student_module_cache.lookup(descriptor.category,
                                                  descriptor.location.url())

    shared_state_key = getattr(descriptor, 'shared_state_key', None)
    if shared_state_key is not None:
        shared_module = student_module_cache.lookup(descriptor.category,
                                                    shared_state_key)
    else:
        shared_module = None

    instance_state = instance_module.state if instance_module is not None else None
    shared_state = shared_module.state if shared_module is not None else None

    # TODO (vshnayder): fix hardcoded urls (use reverse)
    # Setup system context for module instance
    ajax_url = settings.MITX_ROOT_URL + '/modx/' + descriptor.location.url() + '/'

    # Fully qualified callback URL for external queueing system 
    xqueue_callback_url = (request.build_absolute_uri('/') + settings.MITX_ROOT_URL + 
                          'xqueue/' + str(user.id) + '/' + descriptor.location.url() + '/' + 
                          'score_update')

    # Default queuename is course-specific and is derived from the course that 
    #   contains the current module.
    # TODO: Queuename should be derived from 'course_settings.json' of each course
    xqueue_default_queuename = descriptor.location.org + '-' + descriptor.location.course

    def _get_module(location):
        (module, _, _, _) = get_module(user, request, location,
                                       student_module_cache, position)
        return module

    # TODO (cpennington): When modules are shared between courses, the static
    # prefix is going to have to be specific to the module, not the directory
    # that the xml was loaded from
    system = ModuleSystem(track_function=make_track_function(request),
                          render_template=render_to_string,
                          ajax_url=ajax_url,
                          xqueue_callback_url=xqueue_callback_url,
                          xqueue_default_queuename=xqueue_default_queuename.replace(' ','_'),
                          # TODO (cpennington): Figure out how to share info between systems
                          filestore=descriptor.system.resources_fs,
                          get_module=_get_module,
                          user=user,
                          # TODO (cpennington): This should be removed when all html from
                          # a module is coming through get_html and is therefore covered
                          # by the replace_static_urls code below
                          replace_urls=replace_urls,
                          )
    # pass position specified in URL to module through ModuleSystem
    system.set('position', position)

    module = descriptor.xmodule_constructor(system)(instance_state, shared_state)

    module.get_html = replace_static_urls(
        wrap_xmodule(module.get_html, module, 'xmodule_display.html'),
        module.metadata['data_dir']
    )

    if settings.MITX_FEATURES.get('DISPLAY_HISTOGRAMS_TO_STAFF') and user.is_staff:
        module.get_html = add_histogram(module.get_html, module)

    # If StudentModule for this instance wasn't already in the database,
    # and this isn't a guest user, create it.
    if user.is_authenticated():
        if not instance_module:
            instance_module = StudentModule(
                student=user,
                module_type=descriptor.category,
                module_state_key=module.id,
                state=module.get_instance_state(),
                max_grade=module.max_score())
            instance_module.save()
            # Add to cache. The caller and the system context have references
            # to it, so the change persists past the return
            student_module_cache.append(instance_module)
        if not shared_module and shared_state_key is not None:
            shared_module = StudentModule(
                student=user,
                module_type=descriptor.category,
                module_state_key=shared_state_key,
                state=module.get_shared_state())
            shared_module.save()
            student_module_cache.append(shared_module)

    return (module, instance_module, shared_module, descriptor.category)


@csrf_exempt
def xqueue_callback(request, userid, id, dispatch):
    # Parse xqueue response
    get = request.POST.copy()
    try:
        header = json.loads(get['xqueue_header'])
    except Exception as err:
        msg = "Error in xqueue_callback %s: Invalid return format" % err
        raise Exception(msg)

    # Retrieve target StudentModule
    user = User.objects.get(id=userid)

    student_module_cache = StudentModuleCache(user, modulestore().get_item(id))
    instance, instance_module, shared_module, module_type = get_module(request.user, request, id, student_module_cache)

    if instance_module is None:
        log.debug("Couldn't find module '%s' for user '%s'",
                  id, request.user)
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


def modx_dispatch(request, dispatch=None, id=None):
    ''' Generic view for extensions. This is where AJAX calls go.

    Arguments:

      - request -- the django request.
      - dispatch -- the command string to pass through to the module's handle_ajax call
           (e.g. 'problem_reset').  If this string contains '?', only pass
           through the part before the first '?'.
      - id -- the module id. Used to look up the XModule instance
    '''
    # ''' (fix emacs broken parsing)

    student_module_cache = StudentModuleCache(request.user, modulestore().get_item(id))
    instance, instance_module, shared_module, module_type = get_module(request.user, request, id, student_module_cache)

    # Don't track state for anonymous users (who don't have student modules)
    if instance_module is not None:
        oldgrade = instance_module.grade
        old_instance_state = instance_module.state
        old_shared_state = shared_module.state if shared_module is not None else None

    # Let the module handle the AJAX
    try:
        ajax_return = instance.handle_ajax(dispatch, request.POST)
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
