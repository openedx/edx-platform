"""
These views handle all actions in Studio related to import and exporting of
courses
"""

import logging
import os
import re
import shutil
import subprocess
import tarfile
from tempfile import mkdtemp
from path import path
from contextlib import contextmanager

import django.core.exceptions
from django.conf import settings
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django_future.csrf import ensure_csrf_cookie
from django.core.urlresolvers import reverse
from django.core.servers.basehttp import FileWrapper
from django.core.files.temp import NamedTemporaryFile
from django.views.decorators.http import require_http_methods

from mitxmako.shortcuts import render_to_response
from auth.authz import create_all_course_groups

from xmodule.modulestore.xml_importer import import_from_xml
from xmodule.contentstore.django import contentstore
from xmodule.modulestore.xml_exporter import export_to_xml
from xmodule.modulestore.django import modulestore
from xmodule.modulestore import Location
from xmodule.exceptions import SerializationError

from .access import get_location_and_verify_access
from util.json_request import JsonResponse


__all__ = ['import_course', 'generate_export_course', 'export_course']

log = logging.getLogger(__name__)

def safe_escape(s):
    ''' Unique, safe encoding for string. Output string will only have
    alphanumerics and underscores. 
    '''
    return "".join([x if x.isalnum() else "_"+str(ord(x))+"_" for x in s])

# Regex to capture Content-Range header ranges.
CONTENT_RE = re.compile(r"(?P<start>\d{1,11})-(?P<stop>\d{1,11})/(?P<end>\d{1,11})")

class ImportError(Exception):
    def __init__(self, error):
        self.error = error

@contextmanager
def working_directory(path):
    current_dir = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(current_dir)

@contextmanager
def wfile(dirname):
    """
    A with-context which will wipe the directory tree on exit. 
    """
    try:
        yield
    finally:
        shutil.rmtree(dirname)

def import_course_from_directory(data_root, course_subdir, location, user):
    ''' Import a course from a directory defined by data_root/course_subdir 
    Place it in the location specified. 

    This function assumes the permissions have been verified by the caller. 
    '''
    # find the 'course.xml' file
    dirpath = None
    course_dir = os.path.join(data_root, course_subdir)

    def get_all_files(directory):
        """
        For each file in the directory, yield a 2-tuple of (file-name,
        directory-path)
        """
        for dirpath, _dirnames, filenames in os.walk(directory):
            for filename in filenames:
                yield (filename, dirpath)

    def get_dir_for_fname(directory, filename):
        """
        Returns the dirpath for the first file found in the directory
        with the given name.  If there is no file in the directory with
        the specified name, return None.
        """
        for fname, dirpath in get_all_files(directory):
            if fname == filename:
                return dirpath
        return None

    fname = "course.xml"

    dirpath = get_dir_for_fname(course_dir, fname)

    if not dirpath:
        raise ImportError('Could not find the course.xml file in the package.')

    logging.debug('found course.xml at {0}'.format(dirpath))

    if dirpath != course_dir:
        for fname in os.listdir(dirpath):
            shutil.move(os.path.join(dirpath,fname), course_dir)

    _module_store, course_items = import_from_xml(
        modulestore('direct'),
        data_root, 
        [course_subdir],
        load_error_modules=False,
        static_content_store=contentstore(),
        target_location_namespace=location,
        draft_store=modulestore()
    )

    logging.debug('new course at {0}'.format(course_items[0].location))

    create_all_course_groups(user, course_items[0].location)
    logging.debug('created all course groups at {0}'.format(course_items[0].location))

def import_course_from_git(repo_path, git, location, user, ssh_deploy_key=None):
    ''' Load a course from a git repo. 

    repo_path is a local directory we can clone to. 
    git is the git repository. 
    location is the course to be overridden. 

    ssh_deploy_key is an optional key to use when cloning through git
    via ssh. This is a private key which should have read-only access
    to the repo. 
    '''
    os.makedirs(repo_path)
    with wfile(repo_path):
        with working_directory(repo_path):
            if not ssh_deploy_key: 
                os.system("git clone "+git)
            else: 
                # We use popen so we never write have to the deploy key to disk
                #
                # The shell=True is typically bad form, but in this case, it does
                # not matter, since all user input is inside ssh-agent, which needs
                # bash -c regardless. 
                process = subprocess.Popen(["ssh-agent bash -c 'ssh-add -; git clone {git}'".format(git=git)], stdin=subprocess.PIPE, shell=True)
                process.stdin.write(ssh_deploy_key)
                process.stdin.close()
                process.wait()
            dirs = []
            for d in os.listdir(repo_path):
                if os.path.isdir(d):
                    dirs.append(d)
            if len(dirs) != 1:
                raise ImportError("git repo must have exactly one course directory")
            import_course_from_directory(repo_path, dirs[0], location, user)

def import_course_from_file(data_root, course_tarball_path, course_subdir, location, user):
    ''' Import a course from a tar file. 

    course_tarball_path is where the course tarball resides. 
    course_subdir is where we can extract the file. 
    location is the course (org,name,...)
    user is the person uploading the course
    
    ''' 
    # 'Lock' with status info.
    course_dir = data_root / course_subdir
    # status_file = course_dir + ".lock"

    # Do everything from now on in a with-context, to be sure we've
    # properly cleaned up.
    with wfile(course_dir):
        tar_file = tarfile.open(course_tarball_path)
        tar_file.extractall((course_dir + '/').encode('utf-8'))
        import_course_from_directory(data_root, course_subdir, location, user)

@ensure_csrf_cookie
@require_http_methods(("GET", "POST", "PUT"))
@login_required
def import_course(request, org, course, name):
    """
    This method will:
    * Handle a POST request to upload and import a .tar.gz file into a
      specified course
    * Handle a POST request to import a course from github. This
      currently only supports github, but could easily be modified to
      support other aservices. Only supporting alphanumeric repos on
      github avoids issues with proper escaping of arbitrary git
      sources.

    """
    location = get_location_and_verify_access(request, org, course, name)

    # This path is for users who are sending a tarball of course data. 
    # Example command to test this with: 
    # curl http://localhost:9001/EDX/EDX201/import/2013_Winter --cookie "edxloggedin=true; sessionid=887329812981878491abc18970fd52a7; csrftoken=CSJWODSJIer90834uofjh890439hfdjs" -X POST --form "course-data=@2013_Winter.tar.gz" -H "X-CSRFToken: CSJWODSJIer90834uofjh890439hfdjs"
    if request.method == 'POST' and 'course-data' in request.FILES: 
        data_root = path(settings.GITHUB_REPO_ROOT) # E.g. /opt/edx/data
        course_subdir = safe_escape(location.url()) # E.g. i4x_58__47__47_AAPT_47_PHYS101_47_course_47_2013_95_Winter
        course_dir = data_root / course_subdir # E.g. /opt/edx/data/i4x_58__47__47_AAPT_47_PHYS101_47_course_47_2013_95_Winter

        filename = request.FILES['course-data'].name # Name of uploaded file
        if not filename.endswith('.tar.gz') and not filename.endswith('.tgz'):
            return JsonResponse(
                {'ErrMsg': 'We only support uploading a .tar.gz file.'},
                status=415
            )
        temp_filepath = course_dir / "course"+".tar.gz" # Where we put the tarball on the filesystem. 

        if not course_dir.isdir():
            os.mkdir(course_dir)

        logging.debug('importing course to {0}'.format(temp_filepath))

        # Get upload chunks byte ranges
        try:
            matches = CONTENT_RE.search(request.META["HTTP_CONTENT_RANGE"])
            content_range = matches.groupdict()
        except KeyError:    # Single chunk
            # no Content-Range header, so make one that will work
            content_range = {'start': 0, 'stop': 1, 'end': 2}

        # stream out the uploaded files in chunks to disk
        if int(content_range['start']) == 0:
            mode = "wb+"
        else:
            mode = "ab+"
            size = os.path.getsize(temp_filepath)
            # Check to make sure we haven't missed a chunk
            # This shouldn't happen, even if different instances are handling
            # the same session, but it's always better to catch errors earlier.
            if size < int(content_range['start']):
                log.warning(
                    "Reported range %s does not match size downloaded so far %s",
                    content_range['start'],
                    size
                )
                return JsonResponse(
                    {'ErrMsg': 'File upload corrupted. Please try again'},
                    status=409
                )
            # The last request sometimes comes twice. This happens because
            # nginx sends a 499 error code when the response takes too long.
            elif size > int(content_range['stop']) and size == int(content_range['end']):
                return JsonResponse({'ImportStatus': 1})

        with open(temp_filepath, mode) as temp_file:
            for chunk in request.FILES['course-data'].chunks():
                temp_file.write(chunk)

        size = os.path.getsize(temp_filepath)

        if int(content_range['stop']) != int(content_range['end']) - 1:
            # More chunks coming
            return JsonResponse({
                "files": [{
                    "name": filename,
                    "size": size,
                    "deleteUrl": "",
                    "deleteType": "",
                    "url": reverse('import_course', kwargs={
                        'org': location.org,
                        'course': location.course,
                        'name': location.name
                    }),
                    "thumbnailUrl": ""
                }]
            })

        else:   # This was the last chunk.
            try: 
                import_course_from_file(data_root, temp_filepath, course_subdir, location, request.user)
                return JsonResponse({'Status': 'OK'})
            except ImportError as e: 
                return JsonResponse({'ErrMsg': e.error}, status=415)
    elif request.method == 'POST' and request.POST['source'] == 'git': 
        # This path is for importing from a git repository 
        # Sample command to test this with: 
        # curl http://localhost:9001/EDX/EDX201/import/2013_Winter --cookie "edxloggedin=true; sessionid=3897yiudy78346y78edy8237yd78237y; csrftoken=Cisujou2389udw89yu2398dy723yd78y" -X POST --form "server=git@github.com" --form "account=sample" --form "repo=edx201" --form "source=git" --form "deploy_key=@/home/deploy/id_rsa_deploy" -H "X-CSRFToken: Cisujou2389udw89yu2398dy723yd78y"
        if not request.POST['account'].isalnum() or not request.POST['repo'].isalnum(): 
            raise django.core.exceptions.ValidationError("github repo and account must be alphanumeric")
        if not request.POST['server'] == 'git@github.com':
            ## Supporting only alphanumeric repos on github makes it
            ## easy to guarantee we're safely escaping everything
            raise NotImplementedError('Source other than github are not supported at this time')

        repo_path = os.path.join(settings.GITHUB_REPO_ROOT, safe_escape(location.url()))
        git = 'git@github.com:{account}/{repo}.git'.format(account = request.POST['account'], 
                                                             repo = request.POST['repo'])
        if 'deploy_key' in request.FILES:
            ssh_deploy_key = request.FILES['deploy_key'].read()
        else:
            ssh_deploy_key = None
        import_course_from_git(repo_path, git, location, request.user, ssh_deploy_key=ssh_deploy_key)
        return JsonResponse({'Status': 'OK'})
    elif request.method == 'GET': # Should this be a seperate view? 
        course_module = modulestore().get_item(location)

        return render_to_response('import.html', {
            'context_course': course_module,
            'successful_import_redirect_url': reverse('course_index', kwargs={
                'org': location.org,
                'course': location.course,
                'name': location.name,
            })
        })
    else:
        raise django.core.exceptions.ValidationError("Invalid arguments to import/export")


@ensure_csrf_cookie
@login_required
def generate_export_course(request, org, course, name):
    """
    This method will serialize out a course to a .tar.gz file which contains a
    XML-based representation of the course
    """
    location = get_location_and_verify_access(request, org, course, name)
    course_module = modulestore().get_instance(location.course_id, location)
    loc = Location(location)
    export_file = NamedTemporaryFile(prefix=name + '.', suffix=".tar.gz")

    root_dir = path(mkdtemp())

    try:
        export_to_xml(modulestore('direct'), contentstore(), loc, root_dir, name, modulestore())
    except SerializationError, e:
        logging.exception('There was an error exporting course {0}. {1}'.format(course_module.location, unicode(e)))
        unit = None
        failed_item = None
        parent = None
        try:
            failed_item = modulestore().get_instance(course_module.location.course_id, e.location)
            parent_locs = modulestore().get_parent_locations(failed_item.location, course_module.location.course_id)

            if len(parent_locs) > 0:
                parent = modulestore().get_item(parent_locs[0])
                if parent.location.category == 'vertical':
                    unit = parent
        except:
            # if we have a nested exception, then we'll show the more generic error message
            pass

        return render_to_response('export.html', {
            'context_course': course_module,
            'successful_import_redirect_url': '',
            'in_err': True,
            'raw_err_msg': str(e),
            'failed_module': failed_item,
            'unit': unit,
            'edit_unit_url': reverse('edit_unit', kwargs={
                'location': parent.location
            }) if parent else '',
            'course_home_url': reverse('course_index', kwargs={
                'org': org,
                'course': course,
                'name': name
            })
        })
    except Exception, e:
        logging.exception('There was an error exporting course {0}. {1}'.format(course_module.location, unicode(e)))
        return render_to_response('export.html', {
            'context_course': course_module,
            'successful_import_redirect_url': '',
            'in_err': True,
            'unit': None,
            'raw_err_msg': str(e),
            'course_home_url': reverse('course_index', kwargs={
                'org': org,
                'course': course,
                'name': name
            })
        })

    logging.debug('tar file being generated at {0}'.format(export_file.name))
    tar_file = tarfile.open(name=export_file.name, mode='w:gz')
    tar_file.add(root_dir / name, arcname=name)
    tar_file.close()

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
    """
    This method serves up the 'Export Course' page
    """
    location = get_location_and_verify_access(request, org, course, name)

    course_module = modulestore().get_item(location)

    return render_to_response('export.html', {
        'context_course': course_module,
        'successful_import_redirect_url': ''
    })
