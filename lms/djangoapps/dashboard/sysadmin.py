# MITx sysadmin dashboard

import csv
import itertools
import json
import logging
import os
import requests
import string
import subprocess
import time
import urllib

from random import choice
from StringIO import StringIO
from datetime import datetime

from django.conf import settings
from django.contrib.auth.models import User, Group
from django.http import HttpResponse, Http404
from courseware.models import StudentModule
from student.models import CourseEnrollment, CourseEnrollmentAllowed
from student.models import UserProfile, Registration
from external_auth.models import ExternalAuthMap

from courseware.access import (has_access, get_access_group_name,
                               course_beta_test_group_name)
from courseware.courses import get_course_with_access, get_course_by_id

from django.contrib.auth import logout, authenticate, login
from django_future.csrf import ensure_csrf_cookie
from django.views.decorators.cache import cache_control
from mitxmako.shortcuts import render_to_response
from xmodule.course_module import CourseDescriptor
from xmodule.modulestore import Location
from xmodule.modulestore.django import modulestore
from xmodule.contentstore.django import contentstore
from xmodule.modulestore.store_utilities import delete_course

import track.views

log = logging.getLogger(__name__)


def escape(s):
    """escape HTML special characters in string"""
    return str(s).replace('<','&lt;').replace('>','&gt;')

def git_info_for_course(cdir):
    gdir = settings.DATA_DIR / cdir
    info = [gdir,'','']
    if os.path.exists(gdir):
        cmd = "cd %s; git log -1" % gdir
        for k in os.popen(cmd).readlines():
            if 'commit' in k:
                info[0] = k.split()[1]
            elif 'Author' in k:
                info[2] = k.split()[1]
            elif 'Date' in k:
                info[1] = k.split(' ',1)[1].strip()
    return info


def fix_external_auth_map_passwords():
    msg = ''
    for eamap in ExternalAuthMap.objects.all():
        u = eamap.user
        pw = eamap.internal_password
        if u is None:
            continue
        try:
            testuser = authenticate(username=u.username, password=pw)
        except Exception as err:
            msg += "Failed in authenticating %s, error %s\n" % (u,err)
            continue
        if testuser is None:
            msg += "Failed in authenticating %s; " % (u)
            msg += "fixed password"
            u.set_password(pw)
            u.save()
            continue
    if not msg:
        msg = "All ok!"
    return msg

@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
def sysadmin_dashboard(request):
    """
    Sysadmin dashboard.
    
    Provides:
        
        1. enrollment numbers
        2. loading new courses from github
        3. reloading XML from files

    """
    if not request.user.is_staff:
        raise Http404

    msg = ''
    problems = []
    plots = []
    datatable = {}
    
    def_ms = modulestore()
    is_using_mongo = 'mongo' in str(def_ms.__class__)

    if is_using_mongo:
        courses = def_ms.get_courses()
        courses = dict([c.id, c] for c in courses)	# no course directory
    else:
        courses = def_ms.courses.items()

    # the instructor dashboard page is modal: grades, psychometrics, admin
    # keep that state in request.session (defaults to grades mode)
    dash_mode = request.POST.get('dash_mode','')
    if dash_mode:
        request.session['dash_mode'] = dash_mode
    else:
        dash_mode = request.session.get('dash_mode','Status')
    
    # helper functions

    def return_csv(fn, datatable, fp=None):
        if fp is None:
            response = HttpResponse(mimetype='text/csv')
            response['Content-Disposition'] = 'attachment; filename={0}'.format(fn)
        else:
            response = fp
        writer = csv.writer(response, dialect='excel', quotechar='"', quoting=csv.QUOTE_ALL)
        writer.writerow(datatable['header'])
        for datarow in datatable['data']:
            encoded_row = [unicode(s).encode('utf-8') for s in datarow]
            writer.writerow(encoded_row)
        return response

    def get_staff_group(course):
        return get_group(course, 'staff')

    def get_instructor_group(course):
        return get_group(course, 'instructor')

    def get_group(course, groupname):
        grpname = get_access_group_name(course, groupname)
        try:
            group = Group.objects.get(name=grpname)
        except Group.DoesNotExist:
            group = Group(name=grpname)     # create the group
            group.save()
        return group

    # default datatable depends on dash_mode
    
    if dash_mode=='Status':
        datatable = dict(header=['Statistic','Value'],
                         title="Site statistics")
        datatable['data'] = [['Total number of users', User.objects.all().count()]]

    elif dash_mode=='Courses':
        data = []

        #for cdir, course in def_ms.courses.items():
        for cdir, course in courses.items():
            data.append([course.display_name, cdir] + git_info_for_course(cdir))

        datatable = dict(header=['Course Name', 'dir', 'git commit', 'last change', 'last editor'],
                         title="Information about all courses",
                         data=data)

    elif dash_mode=='Enrollment' or dash_mode=="Staffing":
        data = []

        #for cdir, course in def_ms.courses.items():
        for cdir, course in courses.items():
            datum = [course.display_name, course.id]
            datum += [CourseEnrollment.objects.filter(course_id=course.id).count()]
            datum += [get_group(course, 'staff').user_set.all().count()]
            datum += [','.join([x.username for x in get_group(course, 'instructor').user_set.all()])]
            data.append(datum)

        datatable = dict(header=['Course Name', 'course_id', '# enrolled', '# staff', 'instructors'],
                         title="Enrollment information for all courses",
                         data=data)

    # process actions from form POST
    action = request.POST.get('action', '')
    track.views.server_track(request, action, {}, page='sysdashboard')

    if "Download list of all users (csv file)" in action:
        datatable = dict(header=['username', 'email'],
                         title="List of all users",
                         data=[[u.username, u.email] for u in User.objects.all()])
        return return_csv('users_%s.csv' % request.META['SERVER_NAME'],datatable)
        
    elif "Check and repair external Auth Map" in action:
        msg += '<pre>'
        msg += fix_external_auth_map_passwords()
        msg += '</pre>'
        datatable = {}

    elif "Create user" in action:
        uname = request.POST.get('student_uname','').strip()
        name = request.POST.get('student_fullname','').strip()

        def GenPasswd(length=8, chars=string.letters + string.digits):
            return ''.join([choice(chars) for i in range(length)])

        def create_user(uname, name, do_mit=False):
            if not uname:
                return "Must provide username"
            if not name:
                return "Must provide full name"
            msg = ''
            if do_mit:
                if not '@' in uname:
                    email = '%s@MIT.EDU' % uname
                else:
                    email = uname
                if not email.endswith('@MIT.EDU'):
                    msg += 'email must end in @MIT.EDU'
                    return msg
                mit_domain = 'ssl:MIT'
                if ExternalAuthMap.objects.filter(external_id = email, external_domain = mit_domain):
                    msg += "Failed - email %s already exists as external_id" % email
                    return msg
                make_eamap = True
            else:
                email = uname
                if not '@' in email:
                    msg += 'email address required (not username)'
                    return msg
            password = GenPasswd(12)
            user = User(username=uname, email=email, is_active=True)
            user.set_password(password)
            try:
                user.save()
            except IntegrityError:
                msg += "Oops, failed to create user %s, IntegrityError" % user
                return msg
                
            r = Registration()
            r.register(user)
            
            up = UserProfile(user=user)
            up.name = name
            up.save()
            
            if make_eamap:
                credentials = "/C=US/ST=Massachusetts/O=Massachusetts Institute of Technology/OU=Client CA v1/CN=%s/emailAddress=%s" % (name,email)
                eamap = ExternalAuthMap(external_id = email,
                                        external_email = email,
                                        external_domain = mit_domain,
                                        external_name = name,
                                        internal_password = password,
                                        external_credentials = json.dumps(credentials),
                    )
                eamap.user = user
                eamap.dtsignup = datetime.now()
                eamap.save()
            
            msg += "User %s created successfully!" % user
            return msg
            
        msg += create_user(uname, name, do_mit=settings.MITX_FEATURES['AUTH_USE_MIT_CERTIFICATES'])
        datatable = {}


    elif "Delete user" in action:
        uname = request.POST.get('student_uname','').strip()

        def delete_user(uname):
            if not uname:
                return "Must provide username"
            if '@' in uname:
                try:
                    u = User.objects.get(email=uname)
                except Exception, err:
                    msg = "Cannot find user with email address %s" % uname
                    return msg
            else:
                try:
                    u = User.objects.get(username=uname)
                except Exception, err:
                    msg = "Cannot find user with username %s" % uname
                    return msg
            u.delete()
            return "Deleted user %s" % uname

        msg += delete_user(uname)

    elif "Download staff and instructor list (csv file)" in action:
        data = []
        roles = ['instructor','staff']
        #for cdir, course in def_ms.courses.items():
        for cdir, course in courses.items():
            for role in roles:
                for u in get_group(course, role).user_set.all():
                    datum = [course.id, role, u.username, u.email, u.profile.name]
                    data.append(datum)
            
        datatable = dict(header=['course_id', 'role', 'username', 'email', 'full_name'],
                         title="List of all course staff and instructors",
                         data=data)
        return return_csv('staff_%s.csv' % request.META['SERVER_NAME'],datatable)
        

    elif action=="Delete course from site":
        
        course_id = request.POST.get('course_id','').strip()
        ok = False
        if course_id in courses:
            ok = True
            course = courses[course_id]
        else:
            try:
                course = get_course_by_id(course_id)
                ok = True
            except Exception as err:
                msg += "Error - cannot get course with ID %s<br/><pre>%s</pre>" % (course_id, escape(err))

        if ok and not is_using_mongo:
            cdir = course.metadata.get('data_dir', course.location.course)
            def_ms.courses.pop(cdir)

            # now move the directory (don't actually delete it)
            nd = cdir + '_deleted_%s' % int(time.time())
            os.rename(settings.DATA_DIR / cdir, settings.DATA_DIR / nd)
            os.system('chmod -x %s' % (settings.DATA_DIR / nd))

            msg += "<font color='red'>Deleted %s = %s (%s)</font>" % (cdir, course.id, course.display_name)

        elif ok and is_using_mongo:
            # delete course that is stored with mongodb backend
            loc = course.location
            #ms = modulestore('direct')
            cs = contentstore()
            commit = True
            ret = delete_course(def_ms, cs, loc, commit)
            # don't delete user permission groups, though
            msg += "<font color='red'>Deleted %s = %s (%s)</font>" % (loc, course.id, course.display_name)
    

    elif action=="Load new course from github":
        
        gitloc = request.POST.get('repo_location','').strip().replace(' ','').replace(';','')

        def get_course_from_git(gitloc):
            msg = ''
            if (not gitloc.endswith('.git')) or ('http:' in gitloc) or ('https:' in gitloc):
                msg += "The git repo location should end with '.git', and be for SSH access"
                return msg

            if is_using_mongo:
                acscript = getattr(settings, 'CMS_ADD_COURSE_SCRIPT', '')
                if not acscript or not os.path.exists(acscript):
                    msg = "<font color='red'>Must configure CMS_ADD_COURSE_SCRIPT in settings first!</font>"
                    return msg
                cmd = '{0} "{1}"'.format(acscript, gitloc)
                logging.debug('Adding course with command: {0}'.format(cmd))
                ret = subprocess.Popen(cmd, shell=True, executable = "/bin/bash",
                                       stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
                ret = ''.join(ret)
                msg = "<font color='red'>Added course from {0}</font>".format(gitloc)
                msg += "<pre>{0}</pre>".format(ret.replace('<','&lt;'))
                return msg

            cdir = gitloc.rsplit('/',1)[1][:-4]
            gdir = settings.DATA_DIR / cdir
            if os.path.exists(gdir):
                msg += "The course %s already exists in the data directory! (reloading anyway)" % cdir
                # return msg
            else:
                cmd = "cd %s; git clone %s" % (settings.DATA_DIR, gitloc)
                msg += '<pre>%s</pre>' % escape(os.popen(cmd).read())
            if not os.path.exists(gdir):
                msg += "Failed to clone repository to %s" % gdir
                return msg
            def_ms.try_load_course(cdir)	# load into modulestore
            errlog = def_ms.errored_courses.get(cdir,'')
            if errlog:
                msg += '<hr width="50%%"><pre>%s</pre>' % escape(errlog)
            else:
                course = def_ms.courses[cdir]
                msg += "Loaded course %s (%s)<br/>Errors:" % (cdir, course.display_name)
                errors = def_ms.get_item_errors(course.location)
                if not errors:
                    msg += "None"
                else:
                    msg += "<ul>"
                    for (summary, err) in errors:
                        msg += '<li><pre>%s: %s</pre></li>' % (escape(summary), escape(err))
                    msg += "</ul>"
                datatable['data'].append([course.display_name, cdir] + git_info_for_course(cdir))
            return msg
            
        msg += get_course_from_git(gitloc)

    else:	# default to showing status summary
        msg += '<h2>Courses loaded in the modulestore</h2>'
        msg += '<ol>'
        #for cdir, course in def_ms.courses.items():
        for cdir, course in courses.items():
            msg += '<li>%s (%s)</li>' % (escape(cdir),
                                         course.location.url())
        msg += '</ol>'

        
    
    #----------------------------------------
    # context for rendering

    context = {'datatable': datatable,
               'plots': plots,
               'msg': msg,
               'djangopid' : os.getpid(),
               'modeflag': {dash_mode: 'selectedmode'},
               'mitx_version' : getattr(settings,'MITX_VERSION_STRING',''),
               }

    return render_to_response('sysadmin_dashboard.html', context)
    
#-----------------------------------------------------------------------------

def view_git_logs(request, course_id=None):

    import mongoengine	# don't import that until we need it, here

    class CourseImportLog(mongoengine.Document):
        course_id = mongoengine.StringField(max_length=128)
        location = mongoengine.StringField(max_length=168)
        import_log = mongoengine.StringField(max_length=20*65535)
        git_log = mongoengine.StringField(max_length=65535)
        repo_dir = mongoengine.StringField(max_length=128)
        created = mongoengine.DateTimeField()
        meta = { 'indexes': ['course_id', 'created'],
                 'allow_inheritance': False, }

    DBNAME = "xlog"

    mdb = mongoengine.connect(DBNAME)
    
    if course_id is None:
        cilset = CourseImportLog.objects.all().order_by('-created')
    else:
        log.debug('course_id=%s' % course_id)
        cilset = CourseImportLog.objects.filter(course_id=course_id).order_by('-created')
        log.debug('cilset length=%s' % len(cilset))
        
    context = {'cilset': cilset,
               'course_id': course_id,
               }

    return render_to_response('sysadmin_dashboard_gitlogs.html', context)
    
    
    