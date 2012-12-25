import json
import logging
import os
import re
import sys
import traceback
from path import path
import time
import shutil

from fs.osfs import OSFS
from datetime import datetime

from django.http import HttpResponse, Http404, HttpResponseBadRequest, HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.context_processors import csrf
from django_future.csrf import ensure_csrf_cookie
from django.core.urlresolvers import reverse
from django.conf import settings

from .views import has_access

from xmodule.modulestore import Location
from xmodule.modulestore.exceptions import ItemNotFoundError, InvalidLocationError
from xmodule.x_module import ModuleSystem
from xmodule.error_module import ErrorDescriptor
from xmodule.errortracker import exc_info_to_str
from static_replace import replace_urls
from external_auth.views import ssl_login_shortcut

from mitxmako.shortcuts import render_to_response, render_to_string
from xmodule.modulestore.django import modulestore
from xmodule_modifiers import replace_static_urls, wrap_xmodule
from xmodule.exceptions import NotFoundError
from functools import partial

from xmodule.contentstore.django import contentstore
from xmodule.contentstore.content import StaticContent

from cms.djangoapps.models.settings.course_details import CourseDetails,\
    CourseSettingsEncoder
from cms.djangoapps.contentstore.utils import get_modulestore

# from lxml import etree

log = logging.getLogger(__name__)


@ensure_csrf_cookie
@login_required
def export_course(request, org, course, name):

    location = ['i4x', org, course, 'course', name]

    log.debug('in export_course')

    course_module = modulestore().get_item(location)

    log.debug('metadta: %s' % course_module.metadata)

    metadata = course_module.metadata
    if 'export' not in metadata:
        metadata['export'] = {}
    exportinfo = metadata['export']
    
    # get git repo location and branch from course metadata
    git_repo = exportinfo.get('git_repo', "git@github.com:MITx/content-mit-6002x.git")
    git_branch = exportinfo.get('git_branch', "import/studio")
    local_dir = exportinfo.get('local_dir',"content-mit-910x")

    log.debug('local_dir=%s' % local_dir)

    message = ""

    # check that logged in user has permissions to this item
    if not has_access(request.user, location):
        raise PermissionDenied()

    action = request.POST.get('submit','')
    log.debug('action=%s' % action)

    if request.method == 'POST' and action=='Set Git Repository Info':
        git_repo = request.POST['git_repo'].replace(';','_').replace('\n','')
        git_branch = request.POST['git_branch'].replace(';','_').replace('\n','')
        exportinfo['git_repo'] = git_repo
        exportinfo['git_branch'] = git_branch
        log.debug('set export info (%s, %s)' % (git_repo, git_branch))

        m = re.search('/([^/]+)\.git$',git_repo)	# get local_dir from git_repo
        if m:
            local_dir = m.group(1)
            exportinfo['local_dir'] = local_dir

        store = get_modulestore(Location(location));
        store.update_metadata(location, course_module.metadata)	# save in mongodb store
        message = "Git repository information updated"
        message += "\nlocal_dir = %s" % local_dir
            
    elif request.method == 'POST' and action=='Export Now':
        log.debug('doing export now')
        data_root = path(settings.GITHUB_REPO_ROOT)

        course_dir = data_root / local_dir
        message += 'exporting course to %s\n' % course_dir
        log.debug(message)

        if not os.path.exists(course_dir):
            message += "Creating course directory %s\n" % course_dir
            message += os.popen('(cd "%s"; git clone %s) 2>&1' % (data_root, git_repo)).read()
            cmd = '(cd "%s"; git checkout %s; git pull -u) 2>&1' % (course_dir, git_branch)
            message += os.popen(cmd).read()

        if not os.path.exists(course_dir):
            message += "Failed to create course directory!  Starting with empty directory"

        fs = OSFS(course_dir, create=True)
    
        course_details = CourseDetails.fetch(location)
        success = False
        try:
            xml = course_module.export_to_xml(fs)
            with fs.open('course.xml', mode='w') as f:
                f.write(xml)
            with fs.open('metadata.json', mode='w') as f:	# dump course metadata
                f.write(json.dumps(course_module.metadata))
            with fs.open('settings.json', mode='w') as f:	# dump course settings (about page, ...)
                f.write(json.dumps(course_details, cls=CourseSettingsEncoder))
            success = True
        except:
            message += '\nExport failed!'
            traceback.print_exc()
            # return HttpResponse(json.dumps({'ErrMsg': 'export failed'}))
    
        if success:
            # export done; now issue the git commit, git push, and hub pull-request
            msg = "import from studio %s by %s" % (datetime.now(),request.user)
            cmd = '('
            cmd += 'cd %s' % course_dir
            cmd += '; git add .' 
            cmd += '; git commit -a -m "%s"' % msg
            cmd += '; hub push origin %s' % git_branch
            cmd += '; sleep 2'	# wait for github to update
            cmd += '; hub pull-request "%s" -b master' % msg
            cmd += ') 2>&1'
            ret = os.popen(cmd).read()
            log.debug('git command = %s' % cmd)
            log.debug('return from command = %s' % ret)
            message += '\n' + ret

        #return HttpResponse(json.dumps({'Status': 'Msg', 'ErrMsg': ret}))

        # return HttpResponse(json.dumps({'Status': 'OK'}))

    context = {'git_repo' : git_repo,
               'git_branch' : git_branch,
               'context_course': course_module,
               'message' : message,
               'active_tab': 'export',
               }
    return render_to_response('export.html', context)

