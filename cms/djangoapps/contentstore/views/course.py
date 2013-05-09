from django.contrib.auth.decorators import login_required
from django_future.csrf import ensure_csrf_cookie

from util.json_request import expect_json
from mitxmako.shortcuts import render_to_response

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

    # clone a default 'about' module as well

    about_template_location = Location(['i4x', 'edx', 'templates', 'about', 'overview'])
    dest_about_location = dest_location._replace(category='about', name='overview')
    modulestore('direct').clone_item(about_template_location, dest_about_location)

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
                                                     [course_subdir], load_error_modules=False,
                                                     static_content_store=contentstore(),
                                                     target_location_namespace=Location(location),
                                                     draft_store=modulestore())

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

    export_to_xml(modulestore('direct'), contentstore(), loc, root_dir, name, modulestore())
    #filename = root_dir / name + '.tar.gz'

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

