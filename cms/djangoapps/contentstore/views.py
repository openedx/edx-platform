from util.json_request import expect_json
import json
import logging
import os
import sys
import time
import tarfile
import shutil
from collections import defaultdict
from uuid import uuid4
from path import path
from xmodule.modulestore.xml_exporter import export_to_xml
from tempfile import mkdtemp
from django.core.servers.basehttp import FileWrapper
from django.core.files.temp import NamedTemporaryFile

# to install PIL on MacOSX: 'easy_install http://dist.repoze.org/PIL-1.1.6.tar.gz'
from PIL import Image

from django.http import HttpResponse, Http404, HttpResponseBadRequest, HttpResponseForbidden, HttpResponseServerError
from django.http import HttpResponseNotFound
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.context_processors import csrf
from django_future.csrf import ensure_csrf_cookie
from django.core.urlresolvers import reverse
from django.conf import settings

from xmodule.modulestore import Location
from xmodule.modulestore.exceptions import ItemNotFoundError, InvalidLocationError
from xmodule.modulestore.inheritance import own_metadata
from xblock.core import Scope
from xblock.runtime import KeyValueStore, DbModel, InvalidScopeError
from xmodule.x_module import ModuleSystem
from xmodule.error_module import ErrorDescriptor
from xmodule.errortracker import exc_info_to_str
import static_replace
from external_auth.views import ssl_login_shortcut
from xmodule.modulestore.mongo import MongoUsage

from mitxmako.shortcuts import render_to_response, render_to_string
from xmodule.modulestore.django import modulestore
from xmodule_modifiers import replace_static_urls, wrap_xmodule
from xmodule.exceptions import NotFoundError, ProcessingError
from functools import partial

from xmodule.contentstore.django import contentstore
from xmodule.contentstore.content import StaticContent
from xmodule.util.date_utils import get_default_time_display

from auth.authz import is_user_in_course_group_role, get_users_in_course_group_by_role
from auth.authz import get_user_by_email, add_user_to_course_group, remove_user_from_course_group
from auth.authz import INSTRUCTOR_ROLE_NAME, STAFF_ROLE_NAME, create_all_course_groups
from .utils import get_course_location_for_item, get_lms_link_for_item, compute_unit_state, \
    UnitState, get_course_for_item, get_url_reverse, add_open_ended_panel_tab, \
    remove_open_ended_panel_tab

from xmodule.modulestore.xml_importer import import_from_xml
from contentstore.course_info_model import get_course_updates, \
    update_course_updates, delete_course_update
from cache_toolbox.core import del_cached_content
from contentstore.module_info_model import get_module_info, set_module_info
from models.settings.course_details import CourseDetails, \
    CourseSettingsEncoder
from models.settings.course_grading import CourseGradingModel
from contentstore.utils import get_modulestore
from django.shortcuts import redirect
from models.settings.course_metadata import CourseMetadata

# to install PIL on MacOSX: 'easy_install http://dist.repoze.org/PIL-1.1.6.tar.gz'

log = logging.getLogger(__name__)


COMPONENT_TYPES = ['customtag', 'discussion', 'html', 'problem', 'video']

OPEN_ENDED_COMPONENT_TYPES = ["combinedopenended", "peergrading"]
ADVANCED_COMPONENT_TYPES = ['annotatable'] + OPEN_ENDED_COMPONENT_TYPES
ADVANCED_COMPONENT_CATEGORY = 'advanced'
ADVANCED_COMPONENT_POLICY_KEY = 'advanced_modules'

# cdodge: these are categories which should not be parented, they are detached from the hierarchy
DETACHED_CATEGORIES = ['about', 'static_tab', 'course_info']


# ==== Public views ==================================================

@ensure_csrf_cookie
def signup(request):
    """
    Display the signup form.
    """
    csrf_token = csrf(request)['csrf_token']
    return render_to_response('signup.html', {'csrf': csrf_token})


def old_login_redirect(request):
    '''
    Redirect to the active login url.
    '''
    return redirect('login', permanent=True)


@ssl_login_shortcut
@ensure_csrf_cookie
def login_page(request):
    """
    Display the login form.
    """
    csrf_token = csrf(request)['csrf_token']
    return render_to_response('login.html', {
        'csrf': csrf_token,
        'forgot_password_link': "//{base}/#forgot-password-modal".format(base=settings.LMS_BASE),
    })


def howitworks(request):
    if request.user.is_authenticated():
        return index(request)
    else:
        return render_to_response('howitworks.html', {})

# ==== Views for any logged-in user ==================================


@login_required
@ensure_csrf_cookie
def index(request):
    """
    List all courses available to the logged in user
    """
    courses = modulestore('direct').get_items(['i4x', None, None, 'course', None])

    # filter out courses that we don't have access too
    def course_filter(course):
        return (has_access(request.user, course.location)
                and course.location.course != 'templates'
                and course.location.org != ''
                and course.location.course != ''
                and course.location.name != '')
    courses = filter(course_filter, courses)

    return render_to_response('index.html', {
        'new_course_template': Location('i4x', 'edx', 'templates', 'course', 'Empty'),
        'courses': [(course.display_name,
                    get_url_reverse('CourseOutline', course),
                    get_lms_link_for_item(course.location, course_id=course.location.course_id))
                    for course in courses],
        'user': request.user,
        'disable_course_creation': settings.MITX_FEATURES.get('DISABLE_COURSE_CREATION', False) and not request.user.is_staff
    })


# ==== Views with per-item permissions================================


def has_access(user, location, role=STAFF_ROLE_NAME):
    '''
    Return True if user allowed to access this piece of data
    Note that the CMS permissions model is with respect to courses
    There is a super-admin permissions if user.is_staff is set
    Also, since we're unifying the user database between LMS and CAS,
    I'm presuming that the course instructor (formally known as admin)
    will not be in both INSTRUCTOR and STAFF groups, so we have to cascade our queries here as INSTRUCTOR
    has all the rights that STAFF do
    '''
    course_location = get_course_location_for_item(location)
    _has_access = is_user_in_course_group_role(user, course_location, role)
    # if we're not in STAFF, perhaps we're in INSTRUCTOR groups
    if not _has_access and role == STAFF_ROLE_NAME:
        _has_access = is_user_in_course_group_role(user, course_location, INSTRUCTOR_ROLE_NAME)
    return _has_access


@login_required
@ensure_csrf_cookie
def course_index(request, org, course, name):
    """
    Display an editable course overview.

    org, course, name: Attributes of the Location for the item to edit
    """
    location = get_location_and_verify_access(request, org, course, name)

    lms_link = get_lms_link_for_item(location)

    upload_asset_callback_url = reverse('upload_asset', kwargs={
        'org': org,
        'course': course,
        'coursename': name
    })

    course = modulestore().get_item(location, depth=3)
    sections = course.get_children()

    return render_to_response('overview.html', {
        'active_tab': 'courseware',
        'context_course': course,
        'lms_link': lms_link,
        'sections': sections,
        'course_graders': json.dumps(CourseGradingModel.fetch(course.location).graders),
        'parent_location': course.location,
        'new_section_template': Location('i4x', 'edx', 'templates', 'chapter', 'Empty'),
        'new_subsection_template': Location('i4x', 'edx', 'templates', 'sequential', 'Empty'),  # for now they are the same, but the could be different at some point...
        'upload_asset_callback_url': upload_asset_callback_url,
        'create_new_unit_template': Location('i4x', 'edx', 'templates', 'vertical', 'Empty')
    })


@login_required
def edit_subsection(request, location):
    # check that we have permissions to edit this item
    course = get_course_for_item(location)
    if not has_access(request.user, course.location):
        raise PermissionDenied()

    item = modulestore().get_item(location, depth=1)

    lms_link = get_lms_link_for_item(location, course_id=course.location.course_id)
    preview_link = get_lms_link_for_item(location, course_id=course.location.course_id, preview=True)

    # make sure that location references a 'sequential', otherwise return BadRequest
    if item.location.category != 'sequential':
        return HttpResponseBadRequest()

    parent_locs = modulestore().get_parent_locations(location, None)

    # we're for now assuming a single parent
    if len(parent_locs) != 1:
        logging.error('Multiple (or none) parents have been found for {0}'.format(location))

    # this should blow up if we don't find any parents, which would be erroneous
    parent = modulestore().get_item(parent_locs[0])

    # remove all metadata from the generic dictionary that is presented in a more normalized UI

    policy_metadata = dict(
        (field.name, field.read_from(item))
        for field
        in item.fields
        if field.name not in ['display_name', 'start', 'due', 'format'] and
            field.scope == Scope.settings
    )

    can_view_live = False
    subsection_units = item.get_children()
    for unit in subsection_units:
        state = compute_unit_state(unit)
        if state == UnitState.public or state == UnitState.draft:
            can_view_live = True
            break

    return render_to_response('edit_subsection.html',
        {'subsection': item,
         'context_course': course,
         'create_new_unit_template': Location('i4x', 'edx', 'templates', 'vertical', 'Empty'),
         'lms_link': lms_link,
         'preview_link': preview_link,
         'course_graders': json.dumps(CourseGradingModel.fetch(course.location).graders),
         'parent_location': course.location,
         'parent_item': parent,
         'policy_metadata': policy_metadata,
         'subsection_units': subsection_units,
         'can_view_live': can_view_live
        })


@login_required
def edit_unit(request, location):
    """
    Display an editing page for the specified module.

    Expects a GET request with the parameter 'id'.

    id: A Location URL
    """
    course = get_course_for_item(location)
    if not has_access(request.user, course.location):
        raise PermissionDenied()

    item = modulestore().get_item(location, depth=1)

    lms_link = get_lms_link_for_item(item.location, course_id=course.location.course_id)

    component_templates = defaultdict(list)

    # Check if there are any advanced modules specified in the course policy. These modules
    # should be specified as a list of strings, where the strings are the names of the modules
    # in ADVANCED_COMPONENT_TYPES that should be enabled for the course.
    course_advanced_keys = course.advanced_modules

    # Set component types according to course policy file
    component_types = list(COMPONENT_TYPES)
    if isinstance(course_advanced_keys, list):
        course_advanced_keys = [c for c in course_advanced_keys if c in ADVANCED_COMPONENT_TYPES]
        if len(course_advanced_keys) > 0:
            component_types.append(ADVANCED_COMPONENT_CATEGORY)
    else:
        log.error("Improper format for course advanced keys! {0}".format(course_advanced_keys))

    templates = modulestore().get_items(Location('i4x', 'edx', 'templates'))
    for template in templates:
        category = template.location.category

        if category in course_advanced_keys:
            category = ADVANCED_COMPONENT_CATEGORY

        if category in component_types:
            # This is a hack to create categories for different xmodules
            component_templates[category].append((
                template.display_name_with_default,
                template.location.url(),
                hasattr(template, 'markdown') and template.markdown is not None,
                template.cms.empty,
            ))

    components = [
        component.location.url()
        for component
        in item.get_children()
    ]

    # TODO (cpennington): If we share units between courses,
    # this will need to change to check permissions correctly so as
    # to pick the correct parent subsection

    containing_subsection_locs = modulestore().get_parent_locations(location, None)
    containing_subsection = modulestore().get_item(containing_subsection_locs[0])

    containing_section_locs = modulestore().get_parent_locations(containing_subsection.location, None)
    containing_section = modulestore().get_item(containing_section_locs[0])

    # cdodge hack. We're having trouble previewing drafts via jump_to redirect
    # so let's generate the link url here

    # need to figure out where this item is in the list of children as the preview will need this
    index = 1
    for child in containing_subsection.get_children():
        if child.location == item.location:
            break
        index = index + 1

    preview_lms_base = settings.MITX_FEATURES.get('PREVIEW_LMS_BASE',
        'preview.' + settings.LMS_BASE)

    preview_lms_link = '//{preview_lms_base}/courses/{org}/{course}/{course_name}/courseware/{section}/{subsection}/{index}'.format(
            preview_lms_base=preview_lms_base,
            lms_base=settings.LMS_BASE,
            org=course.location.org,
            course=course.location.course,
            course_name=course.location.name,
            section=containing_section.location.name,
            subsection=containing_subsection.location.name,
            index=index)

    unit_state = compute_unit_state(item)

    return render_to_response('unit.html', {
        'context_course': course,
        'active_tab': 'courseware',
        'unit': item,
        'unit_location': location,
        'components': components,
        'component_templates': component_templates,
        'draft_preview_link': preview_lms_link,
        'published_preview_link': lms_link,
        'subsection': containing_subsection,
        'release_date': get_default_time_display(containing_subsection.lms.start) if containing_subsection.lms.start is not None else None,
        'section': containing_section,
        'create_new_unit_template': Location('i4x', 'edx', 'templates', 'vertical', 'Empty'),
        'unit_state': unit_state,
        'published_date': item.cms.published_date.strftime('%B %d, %Y') if item.cms.published_date is not None else None,
    })


@login_required
def preview_component(request, location):
    # TODO (vshnayder): change name from id to location in coffee+html as well.
    if not has_access(request.user, location):
        raise HttpResponseForbidden()

    component = modulestore().get_item(location)

    return render_to_response('component.html', {
        'preview': get_module_previews(request, component)[0],
        'editor': wrap_xmodule(component.get_html, component, 'xmodule_edit.html')(),
    })


@expect_json
@login_required
@ensure_csrf_cookie
def assignment_type_update(request, org, course, category, name):
    '''
    CRUD operations on assignment types for sections and subsections and anything else gradable.
    '''
    location = Location(['i4x', org, course, category, name])
    if not has_access(request.user, location):
        raise HttpResponseForbidden()

    if request.method == 'GET':
        return HttpResponse(json.dumps(CourseGradingModel.get_section_grader_type(location)),
                            mimetype="application/json")
    elif request.method == 'POST':  # post or put, doesn't matter.
        return HttpResponse(json.dumps(CourseGradingModel.update_section_grader_type(location, request.POST)),
                            mimetype="application/json")


def user_author_string(user):
    '''Get an author string for commits by this user.  Format:
    first last <email@email.com>.

    If the first and last names are blank, uses the username instead.
    Assumes that the email is not blank.
    '''
    f = user.first_name
    l = user.last_name
    if f == '' and l == '':
        f = user.username
    return '{first} {last} <{email}>'.format(first=f,
                                             last=l,
                                             email=user.email)


@login_required
def preview_dispatch(request, preview_id, location, dispatch=None):
    """
    Dispatch an AJAX action to a preview XModule

    Expects a POST request, and passes the arguments to the module

    preview_id (str): An identifier specifying which preview this module is used for
    location: The Location of the module to dispatch to
    dispatch: The action to execute
    """

    descriptor = modulestore().get_item(location)
    instance = load_preview_module(request, preview_id, descriptor)
    # Let the module handle the AJAX
    try:
        ajax_return = instance.handle_ajax(dispatch, request.POST)

    except NotFoundError:
        log.exception("Module indicating to user that request doesn't exist")
        raise Http404

    except ProcessingError:
        log.warning("Module raised an error while processing AJAX request",
                    exc_info=True)
        return HttpResponseBadRequest()

    except:
        log.exception("error processing ajax call")
        raise

    return HttpResponse(ajax_return)


def render_from_lms(template_name, dictionary, context=None, namespace='main'):
    """
    Render a template using the LMS MAKO_TEMPLATES
    """
    return render_to_string(template_name, dictionary, context, namespace="lms." + namespace)


class SessionKeyValueStore(KeyValueStore):
    def __init__(self, request, model_data):
        self._model_data = model_data
        self._session = request.session

    def get(self, key):
        try:
            return self._model_data[key.field_name]
        except (KeyError, InvalidScopeError):
            return self._session[tuple(key)]

    def set(self, key, value):
        try:
            self._model_data[key.field_name] = value
        except (KeyError, InvalidScopeError):
            self._session[tuple(key)] = value

    def delete(self, key):
        try:
            del self._model_data[key.field_name]
        except (KeyError, InvalidScopeError):
            del self._session[tuple(key)]

    def has(self, key):
        return key in self._model_data or key in self._session


def preview_module_system(request, preview_id, descriptor):
    """
    Returns a ModuleSystem for the specified descriptor that is specialized for
    rendering module previews.

    request: The active django request
    preview_id (str): An identifier specifying which preview this module is used for
    descriptor: An XModuleDescriptor
    """

    def preview_model_data(descriptor):
        return DbModel(
            SessionKeyValueStore(request, descriptor._model_data),
            descriptor.module_class,
            preview_id,
            MongoUsage(preview_id, descriptor.location.url()),
        )

    return ModuleSystem(
        ajax_url=reverse('preview_dispatch', args=[preview_id, descriptor.location.url(), '']).rstrip('/'),
        # TODO (cpennington): Do we want to track how instructors are using the preview problems?
        track_function=lambda type, event: None,
        filestore=descriptor.system.resources_fs,
        get_module=partial(get_preview_module, request, preview_id),
        render_template=render_from_lms,
        debug=True,
        replace_urls=partial(static_replace.replace_static_urls, data_directory=None, course_namespace=descriptor.location),
        user=request.user,
        xblock_model_data=preview_model_data,
    )


def get_preview_module(request, preview_id, descriptor):
    """
    Returns a preview XModule at the specified location. The preview_data is chosen arbitrarily
    from the set of preview data for the descriptor specified by Location

    request: The active django request
    preview_id (str): An identifier specifying which preview this module is used for
    location: A Location
    """

    return load_preview_module(request, preview_id, descriptor)


def load_preview_module(request, preview_id, descriptor):
    """
    Return a preview XModule instantiated from the supplied descriptor, instance_state, and shared_state

    request: The active django request
    preview_id (str): An identifier specifying which preview this module is used for
    descriptor: An XModuleDescriptor
    instance_state: An instance state string
    shared_state: A shared state string
    """
    system = preview_module_system(request, preview_id, descriptor)
    try:
        module = descriptor.xmodule(system)
    except:
        log.debug("Unable to load preview module", exc_info=True)
        module = ErrorDescriptor.from_descriptor(
            descriptor,
            error_msg=exc_info_to_str(sys.exc_info())
        ).xmodule(system)

    # cdodge: Special case
    if module.location.category == 'static_tab':
        module.get_html = wrap_xmodule(
            module.get_html,
            module,
            "xmodule_tab_display.html",
        )
    else:
        module.get_html = wrap_xmodule(
            module.get_html,
            module,
            "xmodule_display.html",
        )

    module.get_html = replace_static_urls(
        module.get_html,
        getattr(module, 'data_dir', module.location.course),
        course_namespace=Location([module.location.tag, module.location.org, module.location.course, None, None])
    )

    return module


def get_module_previews(request, descriptor):
    """
    Returns a list of preview XModule html contents. One preview is returned for each
    pair of states returned by get_sample_state() for the supplied descriptor.

    descriptor: An XModuleDescriptor
    """
    preview_html = []
    for idx, (instance_state, shared_state) in enumerate(descriptor.get_sample_state()):
        module = load_preview_module(request, str(idx), descriptor)
        preview_html.append(module.get_html())
    return preview_html


def _xmodule_recurse(item, action):
    for child in item.get_children():
        _xmodule_recurse(child, action)

    action(item)


@login_required
@expect_json
def delete_item(request):
    item_location = request.POST['id']
    item_loc = Location(item_location)

    # check permissions for this user within this course
    if not has_access(request.user, item_location):
        raise PermissionDenied()

    # optional parameter to delete all children (default False)
    delete_children = request.POST.get('delete_children', False)
    delete_all_versions = request.POST.get('delete_all_versions', False)

    item = modulestore().get_item(item_location)

    store = get_modulestore(item_loc)


    # @TODO: this probably leaves draft items dangling. My preferance would be for the semantic to be
    # if item.location.revision=None, then delete both draft and published version
    # if caller wants to only delete the draft than the caller should put item.location.revision='draft'

    if delete_children:
        _xmodule_recurse(item, lambda i: store.delete_item(i.location))
    else:
        store.delete_item(item.location)

    # cdodge: this is a bit of a hack until I can talk with Cale about the
    # semantics of delete_item whereby the store is draft aware. Right now calling
    # delete_item on a vertical tries to delete the draft version leaving the
    # requested delete to never occur
    if item.location.revision is None and item.location.category == 'vertical' and delete_all_versions:
        modulestore('direct').delete_item(item.location)

    # cdodge: we need to remove our parent's pointer to us so that it is no longer dangling
    if delete_all_versions:
        parent_locs = modulestore('direct').get_parent_locations(item_loc, None)

        for parent_loc in parent_locs:
            parent = modulestore('direct').get_item(parent_loc)
            item_url = item_loc.url()
            if item_url in parent.children:
                children = parent.children
                children.remove(item_url)
                parent.children = children
                modulestore('direct').update_children(parent.location, parent.children)

    return HttpResponse()


@login_required
@expect_json
def save_item(request):
    item_location = request.POST['id']

    # check permissions for this user within this course
    if not has_access(request.user, item_location):
        raise PermissionDenied()

    store = get_modulestore(Location(item_location));

    if request.POST.get('data') is not None:
        data = request.POST['data']
        store.update_item(item_location, data)

    # cdodge: note calling request.POST.get('children') will return None if children is an empty array
    # so it lead to a bug whereby the last component to be deleted in the UI was not actually
    # deleting the children object from the children collection
    if 'children' in request.POST and request.POST['children'] is not None:
        children = request.POST['children']
        store.update_children(item_location, children)

    # cdodge: also commit any metadata which might have been passed along in the
    # POST from the client, if it is there
    # NOTE, that the postback is not the complete metadata, as there's system metadata which is
    # not presented to the end-user for editing. So let's fetch the original and
    # 'apply' the submitted metadata, so we don't end up deleting system metadata
    if request.POST.get('metadata') is not None:
        posted_metadata = request.POST['metadata']
        # fetch original
        existing_item = modulestore().get_item(item_location)

        # update existing metadata with submitted metadata (which can be partial)
        # IMPORTANT NOTE: if the client passed pack 'null' (None) for a piece of metadata that means 'remove it'
        for metadata_key, value in posted_metadata.items():

            # let's strip out any metadata fields from the postback which have been identified as system metadata
            # and therefore should not be user-editable, so we should accept them back from the client
            if metadata_key in existing_item.system_metadata_fields:
                del posted_metadata[metadata_key]
            elif posted_metadata[metadata_key] is None:
                # remove both from passed in collection as well as the collection read in from the modulestore
                if metadata_key in existing_item._model_data:
                    del existing_item._model_data[metadata_key]
                del posted_metadata[metadata_key]
            else:
                existing_item._model_data[metadata_key] = value

        # commit to datastore
        # TODO (cpennington): This really shouldn't have to do this much reaching in to get the metadata
        store.update_metadata(item_location, own_metadata(existing_item))

    return HttpResponse()


@login_required
@expect_json
def create_draft(request):
    location = request.POST['id']

    # check permissions for this user within this course
    if not has_access(request.user, location):
        raise PermissionDenied()

    # This clones the existing item location to a draft location (the draft is implicit,
    # because modulestore is a Draft modulestore)
    modulestore().clone_item(location, location)

    return HttpResponse()


@login_required
@expect_json
def publish_draft(request):
    location = request.POST['id']

    # check permissions for this user within this course
    if not has_access(request.user, location):
        raise PermissionDenied()

    item = modulestore().get_item(location)
    _xmodule_recurse(item, lambda i: modulestore().publish(i.location, request.user.id))

    return HttpResponse()


@login_required
@expect_json
def unpublish_unit(request):
    location = request.POST['id']

    # check permissions for this user within this course
    if not has_access(request.user, location):
        raise PermissionDenied()

    item = modulestore().get_item(location)
    _xmodule_recurse(item, lambda i: modulestore().unpublish(i.location))

    return HttpResponse()


@login_required
@expect_json
def clone_item(request):
    parent_location = Location(request.POST['parent_location'])
    template = Location(request.POST['template'])

    display_name = request.POST.get('display_name')

    if not has_access(request.user, parent_location):
        raise PermissionDenied()

    parent = get_modulestore(template).get_item(parent_location)
    dest_location = parent_location._replace(category=template.category, name=uuid4().hex)

    new_item = get_modulestore(template).clone_item(template, dest_location)

    # replace the display name with an optional parameter passed in from the caller
    if display_name is not None:
        new_item.display_name = display_name

    get_modulestore(template).update_metadata(new_item.location.url(), own_metadata(new_item))

    if new_item.location.category not in DETACHED_CATEGORIES:
        get_modulestore(parent.location).update_children(parent_location, parent.children + [new_item.location.url()])

    return HttpResponse(json.dumps({'id': dest_location.url()}))


def upload_asset(request, org, course, coursename):
    '''
    cdodge: this method allows for POST uploading of files into the course asset library, which will
    be supported by GridFS in MongoDB.
    '''
    if request.method != 'POST':
        # (cdodge) @todo: Is there a way to do a - say - 'raise Http400'?
        return HttpResponseBadRequest()

    # construct a location from the passed in path
    location = get_location_and_verify_access(request, org, course, coursename)

    # Does the course actually exist?!? Get anything from it to prove its existance

    try:
        item = modulestore().get_item(location)
    except:
        # no return it as a Bad Request response
        logging.error('Could not find course' + location)
        return HttpResponseBadRequest()

    # compute a 'filename' which is similar to the location formatting, we're using the 'filename'
    # nomenclature since we're using a FileSystem paradigm here. We're just imposing
    # the Location string formatting expectations to keep things a bit more consistent

    filename = request.FILES['file'].name
    mime_type = request.FILES['file'].content_type
    filedata = request.FILES['file'].read()

    content_loc = StaticContent.compute_location(org, course, filename)
    content = StaticContent(content_loc, filename, mime_type, filedata)

    # first let's see if a thumbnail can be created
    (thumbnail_content, thumbnail_location) = contentstore().generate_thumbnail(content)

    # delete cached thumbnail even if one couldn't be created this time (else the old thumbnail will continue to show)
    del_cached_content(thumbnail_location)
    # now store thumbnail location only if we could create it
    if thumbnail_content is not None:
        content.thumbnail_location = thumbnail_location

    # then commit the content
    contentstore().save(content)
    del_cached_content(content.location)

    # readback the saved content - we need the database timestamp
    readback = contentstore().find(content.location)

    response_payload = {'displayname': content.name,
        'uploadDate': get_default_time_display(readback.last_modified_at.timetuple()),
        'url': StaticContent.get_url_path_from_location(content.location),
        'thumb_url': StaticContent.get_url_path_from_location(thumbnail_location) if thumbnail_content is not None else None,
        'msg': 'Upload completed'
        }

    response = HttpResponse(json.dumps(response_payload))
    response['asset_url'] = StaticContent.get_url_path_from_location(content.location)
    return response


'''
This view will return all CMS users who are editors for the specified course
'''
@login_required
@ensure_csrf_cookie
def manage_users(request, location):

    # check that logged in user has permissions to this item
    if not has_access(request.user, location, role=INSTRUCTOR_ROLE_NAME) and not has_access(request.user, location, role=STAFF_ROLE_NAME):
        raise PermissionDenied()

    course_module = modulestore().get_item(location)

    return render_to_response('manage_users.html', {
        'active_tab': 'users',
        'context_course': course_module,
        'staff': get_users_in_course_group_by_role(location, STAFF_ROLE_NAME),
        'add_user_postback_url': reverse('add_user', args=[location]).rstrip('/'),
        'remove_user_postback_url': reverse('remove_user', args=[location]).rstrip('/'),
        'allow_actions': has_access(request.user, location, role=INSTRUCTOR_ROLE_NAME),
        'request_user_id': request.user.id
    })


def create_json_response(errmsg=None):
    if errmsg is not None:
        resp = HttpResponse(json.dumps({'Status': 'Failed', 'ErrMsg': errmsg}))
    else:
        resp = HttpResponse(json.dumps({'Status': 'OK'}))

    return resp


'''
This POST-back view will add a user - specified by email - to the list of editors for
the specified course
'''
@expect_json
@login_required
@ensure_csrf_cookie
def add_user(request, location):
    email = request.POST["email"]

    if email == '':
        return create_json_response('Please specify an email address.')

    # check that logged in user has admin permissions to this course
    if not has_access(request.user, location, role=INSTRUCTOR_ROLE_NAME):
        raise PermissionDenied()

    user = get_user_by_email(email)

    # user doesn't exist?!? Return error.
    if user is None:
        return create_json_response('Could not find user by email address \'{0}\'.'.format(email))

    # user exists, but hasn't activated account?!?
    if not user.is_active:
        return create_json_response('User {0} has registered but has not yet activated his/her account.'.format(email))

    # ok, we're cool to add to the course group
    add_user_to_course_group(request.user, user, location, STAFF_ROLE_NAME)

    return create_json_response()


'''
This POST-back view will remove a user - specified by email - from the list of editors for
the specified course
'''
@expect_json
@login_required
@ensure_csrf_cookie
def remove_user(request, location):
    email = request.POST["email"]

    # check that logged in user has admin permissions on this course
    if not has_access(request.user, location, role=INSTRUCTOR_ROLE_NAME):
        raise PermissionDenied()

    user = get_user_by_email(email)
    if user is None:
        return create_json_response('Could not find user by email address \'{0}\'.'.format(email))

    # make sure we're not removing ourselves
    if user.id == request.user.id:
        raise PermissionDenied()

    remove_user_from_course_group(request.user, user, location, STAFF_ROLE_NAME)

    return create_json_response()


# points to the temporary course landing page with log in and sign up
def landing(request, org, course, coursename):
    return render_to_response('temp-course-landing.html', {})


@login_required
@ensure_csrf_cookie
def static_pages(request, org, course, coursename):

    location = get_location_and_verify_access(request, org, course, coursename)

    course = modulestore().get_item(location)

    return render_to_response('static-pages.html', {
        'active_tab': 'pages',
        'context_course': course,
    })


def edit_static(request, org, course, coursename):
    return render_to_response('edit-static-page.html', {})


@login_required
@expect_json
def reorder_static_tabs(request):
    tabs = request.POST['tabs']
    course = get_course_for_item(tabs[0])

    if not has_access(request.user, course.location):
        raise PermissionDenied()

    # get list of existing static tabs in course
    # make sure they are the same lengths (i.e. the number of passed in tabs equals the number
    # that we know about) otherwise we can drop some!

    existing_static_tabs = [t for t in course.tabs if t['type'] == 'static_tab']
    if len(existing_static_tabs) != len(tabs):
        return HttpResponseBadRequest()

    # load all reference tabs, return BadRequest if we can't find any of them
    tab_items = []
    for tab in tabs:
        item = modulestore('direct').get_item(Location(tab))
        if item is None:
            return HttpResponseBadRequest()

        tab_items.append(item)

    # now just go through the existing course_tabs and re-order the static tabs
    reordered_tabs = []
    static_tab_idx = 0
    for tab in course.tabs:
        if tab['type'] == 'static_tab':
            reordered_tabs.append({'type': 'static_tab',
                'name': tab_items[static_tab_idx].display_name,
                'url_slug': tab_items[static_tab_idx].location.name})
            static_tab_idx += 1
        else:
            reordered_tabs.append(tab)


    # OK, re-assemble the static tabs in the new order
    course.tabs = reordered_tabs
    modulestore('direct').update_metadata(course.location, own_metadata(course))
    return HttpResponse()


@login_required
@ensure_csrf_cookie
def edit_tabs(request, org, course, coursename):
    location = ['i4x', org, course, 'course', coursename]
    course_item = modulestore().get_item(location)
    static_tabs_loc = Location('i4x', org, course, 'static_tab', None)

    # check that logged in user has permissions to this item
    if not has_access(request.user, location):
        raise PermissionDenied()

    # see tabs have been uninitialized (e.g. supporing courses created before tab support in studio)
    if course_item.tabs is None or len(course_item.tabs) == 0:
        initialize_course_tabs(course_item)

    # first get all static tabs from the tabs list
    # we do this because this is also the order in which items are displayed in the LMS
    static_tabs_refs = [t for t in course_item.tabs if t['type'] == 'static_tab']

    static_tabs = []
    for static_tab_ref in static_tabs_refs:
        static_tab_loc = Location(location)._replace(category='static_tab', name=static_tab_ref['url_slug'])
        static_tabs.append(modulestore('direct').get_item(static_tab_loc))

    components = [
        static_tab.location.url()
        for static_tab
        in static_tabs
    ]

    return render_to_response('edit-tabs.html', {
        'active_tab': 'pages',
        'context_course': course_item,
        'components': components
        })


def not_found(request):
    return render_to_response('error.html', {'error': '404'})


def server_error(request):
    return render_to_response('error.html', {'error': '500'})


@login_required
@ensure_csrf_cookie
def course_info(request, org, course, name, provided_id=None):
    """
    Send models and views as well as html for editing the course info to the client.

    org, course, name: Attributes of the Location for the item to edit
    """
    location = get_location_and_verify_access(request, org, course, name)

    course_module = modulestore().get_item(location)

    # get current updates
    location = ['i4x', org, course, 'course_info', "updates"]

    return render_to_response('course_info.html', {
        'active_tab': 'courseinfo-tab',
        'context_course': course_module,
        'url_base': "/" + org + "/" + course + "/",
        'course_updates': json.dumps(get_course_updates(location)),
        'handouts_location': Location(['i4x', org, course, 'course_info', 'handouts']).url()
    })


@expect_json
@login_required
@ensure_csrf_cookie
def course_info_updates(request, org, course, provided_id=None):
    """
    restful CRUD operations on course_info updates.

    org, course: Attributes of the Location for the item to edit
    provided_id should be none if it's new (create) and a composite of the update db id + index otherwise.
    """
    # ??? No way to check for access permission afaik
    # get current updates
    location = ['i4x', org, course, 'course_info', "updates"]

    # Hmmm, provided_id is coming as empty string on create whereas I believe it used to be None :-(
    # Possibly due to my removing the seemingly redundant pattern in urls.py
    if provided_id == '':
        provided_id = None

    # check that logged in user has permissions to this item
    if not has_access(request.user, location):
        raise PermissionDenied()

    real_method = get_request_method(request)

    if request.method == 'GET':
        return HttpResponse(json.dumps(get_course_updates(location)),
            mimetype="application/json")
    elif real_method == 'DELETE':
        try:
            return HttpResponse(json.dumps(delete_course_update(location,
                request.POST, provided_id)), mimetype="application/json")
        except:
            return HttpResponseBadRequest("Failed to delete",
                content_type="text/plain")
    elif request.method == 'POST':
        try:
            return HttpResponse(json.dumps(update_course_updates(location,
                request.POST, provided_id)), mimetype="application/json")
        except:
            return HttpResponseBadRequest("Failed to save",
                content_type="text/plain")


@expect_json
@login_required
@ensure_csrf_cookie
def module_info(request, module_location):
    location = Location(module_location)

    # check that logged in user has permissions to this item
    if not has_access(request.user, location):
        raise PermissionDenied()

    real_method = get_request_method(request)

    rewrite_static_links = request.GET.get('rewrite_url_links', 'True') in ['True', 'true']
    logging.debug('rewrite_static_links = {0} {1}'.format(request.GET.get('rewrite_url_links', 'False'), rewrite_static_links))

    # check that logged in user has permissions to this item
    if not has_access(request.user, location):
        raise PermissionDenied()

    if real_method == 'GET':
        return HttpResponse(json.dumps(get_module_info(get_modulestore(location), location, rewrite_static_links=rewrite_static_links)), mimetype="application/json")
    elif real_method == 'POST' or real_method == 'PUT':
        return HttpResponse(json.dumps(set_module_info(get_modulestore(location), location, request.POST)), mimetype="application/json")
    else:
        return HttpResponseBadRequest()


@login_required
@ensure_csrf_cookie
def get_course_settings(request, org, course, name):
    """
    Send models and views as well as html for editing the course settings to the client.

    org, course, name: Attributes of the Location for the item to edit
    """
    location = get_location_and_verify_access(request, org, course, name)

    course_module = modulestore().get_item(location)

    return render_to_response('settings.html', {
        'context_course': course_module,
        'course_location': location,
        'details_url': reverse(course_settings_updates,
                               kwargs={"org": org,
                                       "course": course,
                                       "name": name,
                                       "section": "details"})
    })


@login_required
@ensure_csrf_cookie
def course_config_graders_page(request, org, course, name):
    """
    Send models and views as well as html for editing the course settings to the client.

    org, course, name: Attributes of the Location for the item to edit
    """
    location = get_location_and_verify_access(request, org, course, name)

    course_module = modulestore().get_item(location)
    course_details = CourseGradingModel.fetch(location)

    return render_to_response('settings_graders.html', {
        'context_course': course_module,
        'course_location' : location,
        'course_details': json.dumps(course_details, cls=CourseSettingsEncoder)
    })


@login_required
@ensure_csrf_cookie
def course_config_advanced_page(request, org, course, name):
    """
    Send models and views as well as html for editing the advanced course settings to the client.

    org, course, name: Attributes of the Location for the item to edit
    """
    location = get_location_and_verify_access(request, org, course, name)

    course_module = modulestore().get_item(location)

    return render_to_response('settings_advanced.html', {
        'context_course': course_module,
        'course_location' : location,
        'advanced_dict' : json.dumps(CourseMetadata.fetch(location)),
    })


@expect_json
@login_required
@ensure_csrf_cookie
def course_settings_updates(request, org, course, name, section):
    """
    restful CRUD operations on course settings. This differs from get_course_settings by communicating purely
    through json (not rendering any html) and handles section level operations rather than whole page.

    org, course: Attributes of the Location for the item to edit
    section: one of details, faculty, grading, problems, discussions
    """
    get_location_and_verify_access(request, org, course, name)

    if section == 'details':
        manager = CourseDetails
    elif section == 'grading':
        manager = CourseGradingModel
    else: return

    if request.method == 'GET':
        # Cannot just do a get w/o knowing the course name :-(
        return HttpResponse(json.dumps(manager.fetch(Location(['i4x', org, course, 'course', name])), cls=CourseSettingsEncoder),
                            mimetype="application/json")
    elif request.method == 'POST':  # post or put, doesn't matter.
        return HttpResponse(json.dumps(manager.update_from_json(request.POST), cls=CourseSettingsEncoder),
                            mimetype="application/json")


@expect_json
@login_required
@ensure_csrf_cookie
def course_grader_updates(request, org, course, name, grader_index=None):
    """
    restful CRUD operations on course_info updates. This differs from get_course_settings by communicating purely
    through json (not rendering any html) and handles section level operations rather than whole page.

    org, course: Attributes of the Location for the item to edit
    """

    location = get_location_and_verify_access(request, org, course, name)

    real_method = get_request_method(request)

    if real_method == 'GET':
        # Cannot just do a get w/o knowing the course name :-(
        return HttpResponse(json.dumps(CourseGradingModel.fetch_grader(Location(location), grader_index)),
                            mimetype="application/json")
    elif real_method == "DELETE":
        # ??? Should this return anything? Perhaps success fail?
        CourseGradingModel.delete_grader(Location(location), grader_index)
        return HttpResponse()
    elif request.method == 'POST':   # post or put, doesn't matter.
        return HttpResponse(json.dumps(CourseGradingModel.update_grader_from_json(Location(location), request.POST)),
                            mimetype="application/json")


# # NB: expect_json failed on ["key", "key2"] and json payload
@login_required
@ensure_csrf_cookie
def course_advanced_updates(request, org, course, name):
    """
    restful CRUD operations on metadata. The payload is a json rep of the metadata dicts. For delete, otoh,
    the payload is either a key or a list of keys to delete.

    org, course: Attributes of the Location for the item to edit
    """
    location = get_location_and_verify_access(request, org, course, name)

    real_method = get_request_method(request)

    if real_method == 'GET':
        return HttpResponse(json.dumps(CourseMetadata.fetch(location)), mimetype="application/json")
    elif real_method == 'DELETE':
        return HttpResponse(json.dumps(CourseMetadata.delete_key(location, json.loads(request.body))),
                            mimetype="application/json")
    elif real_method == 'POST' or real_method == 'PUT':
        # NOTE: request.POST is messed up because expect_json cloned_request.POST.copy() is creating a defective entry w/ the whole payload as the key
        request_body = json.loads(request.body)
        #Whether or not to filter the tabs key out of the settings metadata
        filter_tabs = True
        #Check to see if the user instantiated any advanced components.  This is a hack to add the open ended panel tab
        #to a course automatically if the user has indicated that they want to edit the combinedopenended or peergrading
        #module, and to remove it if they have removed the open ended elements.
        if ADVANCED_COMPONENT_POLICY_KEY in request_body:
            #Check to see if the user instantiated any open ended components
            found_oe_type = False
            #Get the course so that we can scrape current tabs
            course_module = modulestore().get_item(location)
            for oe_type in OPEN_ENDED_COMPONENT_TYPES:
                if oe_type in request_body[ADVANCED_COMPONENT_POLICY_KEY]:
                    #Add an open ended tab to the course if needed
                    changed, new_tabs = add_open_ended_panel_tab(course_module)
                    #If a tab has been added to the course, then send the metadata along to CourseMetadata.update_from_json
                    if changed:
                        request_body.update({'tabs': new_tabs})
                        #Indicate that tabs should not be filtered out of the metadata
                        filter_tabs = False
                    #Set this flag to avoid the open ended tab removal code below.
                    found_oe_type = True
                    break
            #If we did not find an open ended module type in the advanced settings,
            # we may need to remove the open ended tab from the course.
            if not found_oe_type:
                #Remove open ended tab to the course if needed
                changed, new_tabs = remove_open_ended_panel_tab(course_module)
                if changed:
                    request_body.update({'tabs': new_tabs})
                    #Indicate that tabs should not be filtered out of the metadata
                    filter_tabs = False
        response_json = json.dumps(CourseMetadata.update_from_json(location, request_body, filter_tabs=filter_tabs))
        return HttpResponse(response_json, mimetype="application/json")

@ensure_csrf_cookie
@login_required
def get_checklists(request, org, course, name):
    """
    Send models, views, and html for displaying the course checklists.

    org, course, name: Attributes of the Location for the item to edit
    """
    location = get_location_and_verify_access(request, org, course, name)

    modulestore = get_modulestore(location)
    course_module = modulestore.get_item(location)
    new_course_template = Location('i4x', 'edx', 'templates', 'course', 'Empty')
    template_module = modulestore.get_item(new_course_template)

    # If course was created before checklists were introduced, copy them over from the template.
    copied = False
    if not course_module.checklists:
        course_module.checklists = template_module.checklists
        copied = True

    checklists, modified = expand_checklist_action_urls(course_module)
    if copied or modified:
        modulestore.update_metadata(location, own_metadata(course_module))
    return render_to_response('checklists.html',
        {
            'context_course': course_module,
            'checklists': checklists
        })


@ensure_csrf_cookie
@login_required
def update_checklist(request, org, course, name, checklist_index=None):
    """
    restful CRUD operations on course checklists. The payload is a json rep of
    the modified checklist. For PUT or POST requests, the index of the
    checklist being modified must be included; the returned payload will
    be just that one checklist. For GET requests, the returned payload
    is a json representation of the list of all checklists.

    org, course, name: Attributes of the Location for the item to edit
    """
    location = get_location_and_verify_access(request, org, course, name)
    modulestore = get_modulestore(location)
    course_module = modulestore.get_item(location)

    real_method = get_request_method(request)
    if real_method == 'POST' or real_method == 'PUT':
        if checklist_index is not None and 0 <= int(checklist_index) < len(course_module.checklists):
            index = int(checklist_index)
            course_module.checklists[index] = json.loads(request.body)
            checklists, modified = expand_checklist_action_urls(course_module)
            modulestore.update_metadata(location, own_metadata(course_module))
            return HttpResponse(json.dumps(checklists[index]), mimetype="application/json")
        else:
            return HttpResponseBadRequest(
                "Could not save checklist state because the checklist index was out of range or unspecified.",
                content_type="text/plain")
    elif request.method == 'GET':
        # In the JavaScript view initialize method, we do a fetch to get all the checklists.
        checklists, modified = expand_checklist_action_urls(course_module)
        if modified:
            modulestore.update_metadata(location, own_metadata(course_module))
        return HttpResponse(json.dumps(checklists), mimetype="application/json")
    else:
        return HttpResponseBadRequest("Unsupported request.", content_type="text/plain")


def expand_checklist_action_urls(course_module):
    """
    Gets the checklists out of the course module and expands their action urls
    if they have not yet been expanded.

    Returns the checklists with modified urls, as well as a boolean
    indicating whether or not the checklists were modified.
    """
    checklists = course_module.checklists
    modified = False
    for checklist in checklists:
        if not checklist.get('action_urls_expanded', False):
            for item in checklist.get('items'):
                item['action_url'] = get_url_reverse(item.get('action_url'), course_module)
            checklist['action_urls_expanded'] = True
            modified = True

    return checklists, modified


@login_required
@ensure_csrf_cookie
def asset_index(request, org, course, name):
    """
    Display an editable asset library

    org, course, name: Attributes of the Location for the item to edit
    """
    location = get_location_and_verify_access(request, org, course, name)

    upload_asset_callback_url = reverse('upload_asset', kwargs={
        'org': org,
        'course': course,
        'coursename': name
    })

    course_module = modulestore().get_item(location)

    course_reference = StaticContent.compute_location(org, course, name)
    assets = contentstore().get_all_content_for_course(course_reference)

    # sort in reverse upload date order
    assets = sorted(assets, key=lambda asset: asset['uploadDate'], reverse=True)

    thumbnails = contentstore().get_all_content_thumbnails_for_course(course_reference)
    asset_display = []
    for asset in assets:
        id = asset['_id']
        display_info = {}
        display_info['displayname'] = asset['displayname']
        display_info['uploadDate'] = get_default_time_display(asset['uploadDate'].timetuple())

        asset_location = StaticContent.compute_location(id['org'], id['course'], id['name'])
        display_info['url'] = StaticContent.get_url_path_from_location(asset_location)

        # note, due to the schema change we may not have a 'thumbnail_location' in the result set
        _thumbnail_location = asset.get('thumbnail_location', None)
        thumbnail_location = Location(_thumbnail_location) if _thumbnail_location is not None else None
        display_info['thumb_url'] = StaticContent.get_url_path_from_location(thumbnail_location) if thumbnail_location is not None else None

        asset_display.append(display_info)

    return render_to_response('asset_index.html', {
        'active_tab': 'assets',
        'context_course': course_module,
        'assets': asset_display,
        'upload_asset_callback_url': upload_asset_callback_url
    })


# points to the temporary edge page
def edge(request):
    return render_to_response('university_profiles/edge.html', {})


@login_required
@expect_json
def create_new_course(request):

    if settings.MITX_FEATURES.get('DISABLE_COURSE_CREATION', False) and not request.user.is_staff:
        raise PermissionDenied()

    # This logic is repeated in xmodule/modulestore/tests/factories.py
    # so if you change anything here, you need to also change it there.
    # TODO: write a test that creates two courses, one with the factory and
    # the other with this method, then compare them to make sure they are
    # equivalent.
    template = Location(request.POST['template'])
    org = request.POST.get('org')
    number = request.POST.get('number')
    display_name = request.POST.get('display_name')

    try:
        dest_location = Location('i4x', org, number, 'course', Location.clean(display_name))
    except InvalidLocationError as e:
        return HttpResponse(json.dumps({'ErrMsg': "Unable to create course '" + display_name + "'.\n\n" + e.message}))

    # see if the course already exists
    existing_course = None
    try:
        existing_course = modulestore('direct').get_item(dest_location)
    except ItemNotFoundError:
        pass

    if existing_course is not None:
        return HttpResponse(json.dumps({'ErrMsg': 'There is already a course defined with this name.'}))

    course_search_location = ['i4x', dest_location.org, dest_location.course, 'course', None]
    courses = modulestore().get_items(course_search_location)

    if len(courses) > 0:
        return HttpResponse(json.dumps({'ErrMsg': 'There is already a course defined with the same organization and course number.'}))

    new_course = modulestore('direct').clone_item(template, dest_location)

    if display_name is not None:
        new_course.display_name = display_name

    # set a default start date to now
    new_course.start = time.gmtime()

    initialize_course_tabs(new_course)

    create_all_course_groups(request.user, new_course.location)

    return HttpResponse(json.dumps({'id': new_course.location.url()}))


def initialize_course_tabs(course):
    # set up the default tabs
    # I've added this because when we add static tabs, the LMS either expects a None for the tabs list or
    # at least a list populated with the minimal times
    # @TODO: I don't like the fact that the presentation tier is away of these data related constraints, let's find a better
    # place for this. Also rather than using a simple list of dictionaries a nice class model would be helpful here

    # This logic is repeated in xmodule/modulestore/tests/factories.py
    # so if you change anything here, you need to also change it there.
    course.tabs = [{"type": "courseware"},
        {"type": "course_info", "name": "Course Info"},
        {"type": "discussion", "name": "Discussion"},
        {"type": "wiki", "name": "Wiki"},
        {"type": "progress", "name": "Progress"}]

    modulestore('direct').update_metadata(course.location.url(), own_metadata(course))


@ensure_csrf_cookie
@login_required
def import_course(request, org, course, name):

    location = get_location_and_verify_access(request, org, course, name)

    if request.method == 'POST':
        filename = request.FILES['course-data'].name

        if not filename.endswith('.tar.gz'):
            return HttpResponse(json.dumps({'ErrMsg': 'We only support uploading a .tar.gz file.'}))

        data_root = path(settings.GITHUB_REPO_ROOT)

        course_subdir = "{0}-{1}-{2}".format(org, course, name)
        course_dir = data_root / course_subdir
        if not course_dir.isdir():
            os.mkdir(course_dir)

        temp_filepath = course_dir / filename

        logging.debug('importing course to {0}'.format(temp_filepath))

        # stream out the uploaded files in chunks to disk
        temp_file = open(temp_filepath, 'wb+')
        for chunk in request.FILES['course-data'].chunks():
            temp_file.write(chunk)
        temp_file.close()

        tf = tarfile.open(temp_filepath)
        tf.extractall(course_dir + '/')

        # find the 'course.xml' file

        for r, d, f in os.walk(course_dir):
            for files in f:
                if files == 'course.xml':
                    break
            if files == 'course.xml':
                break

        if files != 'course.xml':
            return HttpResponse(json.dumps({'ErrMsg': 'Could not find the course.xml file in the package.'}))

        logging.debug('found course.xml at {0}'.format(r))

        if r != course_dir:
            for fname in os.listdir(r):
                shutil.move(r / fname, course_dir)

        module_store, course_items = import_from_xml(modulestore('direct'), settings.GITHUB_REPO_ROOT,
            [course_subdir], load_error_modules=False, static_content_store=contentstore(), target_location_namespace=Location(location))

        # we can blow this away when we're done importing.
        shutil.rmtree(course_dir)

        logging.debug('new course at {0}'.format(course_items[0].location))

        create_all_course_groups(request.user, course_items[0].location)

        return HttpResponse(json.dumps({'Status': 'OK'}))
    else:
        course_module = modulestore().get_item(location)

        return render_to_response('import.html', {
            'context_course': course_module,
            'active_tab': 'import',
            'successful_import_redirect_url': get_url_reverse('CourseOutline', course_module)
        })


@ensure_csrf_cookie
@login_required
def generate_export_course(request, org, course, name):
    location = get_location_and_verify_access(request, org, course, name)

    loc = Location(location)
    export_file = NamedTemporaryFile(prefix=name + '.', suffix=".tar.gz")

    root_dir = path(mkdtemp())

    # export out to a tempdir

    logging.debug('root = {0}'.format(root_dir))

    export_to_xml(modulestore('direct'), contentstore(), loc, root_dir, name)
    # filename = root_dir / name + '.tar.gz'

    logging.debug('tar file being generated at {0}'.format(export_file.name))
    tf = tarfile.open(name=export_file.name, mode='w:gz')
    tf.add(root_dir / name, arcname=name)
    tf.close()

    # remove temp dir
    shutil.rmtree(root_dir / name)

    wrapper = FileWrapper(export_file)
    response = HttpResponse(wrapper, content_type='application/x-tgz')
    response['Content-Disposition'] = 'attachment; filename=%s' % os.path.basename(export_file.name)
    response['Content-Length'] = os.path.getsize(export_file.name)
    return response


@ensure_csrf_cookie
@login_required
def export_course(request, org, course, name):

    location = get_location_and_verify_access(request, org, course, name)

    course_module = modulestore().get_item(location)

    return render_to_response('export.html', {
        'context_course': course_module,
        'active_tab': 'export',
        'successful_import_redirect_url': ''
    })


def event(request):
    '''
    A noop to swallow the analytics call so that cms methods don't spook and poor developers looking at
    console logs don't get distracted :-)
    '''
    return HttpResponse(True)


def render_404(request):
    return HttpResponseNotFound(render_to_string('404.html', {}))


def render_500(request):
    return HttpResponseServerError(render_to_string('500.html', {}))


def get_location_and_verify_access(request, org, course, name):
    """
    Create the location tuple verify that the user has permissions
    to view the location. Returns the location.
    """
    location = ['i4x', org, course, 'course', name]

    # check that logged in user has permissions to this item
    if not has_access(request.user, location):
        raise PermissionDenied()

    return location


def get_request_method(request):
    """
    Using HTTP_X_HTTP_METHOD_OVERRIDE, in the request metadata, determine
    what type of request came from the client, and return it.
    """
    # NB: we're setting Backbone.emulateHTTP to true on the client so everything comes as a post!!!
    if request.method == 'POST' and 'HTTP_X_HTTP_METHOD_OVERRIDE' in request.META:
        real_method = request.META['HTTP_X_HTTP_METHOD_OVERRIDE']
    else:
        real_method = request.method

    return real_method
