#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# pylint: disable-msg=C0111
# python script to pull a git repo and import into cms / edge mongodb content database.
#
# usage:
#
#    python git_add_course.py <git-ssh-url> [<directory>]
#
# argument is git ssh url, like: git@github.com:mitocw/edx4edx_lite.git
# if the directory is given, that is used and presumed to contain the git repo
#

import os
import sys
import re
import datetime
import mongoengine  # used to store import log
import StringIO
import logging

from django.utils.translation import ugettext as _

from django.conf import settings
from django.core import management
from django.core.management.base import CommandError
from xmodule.modulestore.django import modulestore

log = logging.getLogger(__name__)

GIT_REPO_DIR = getattr(settings,
                       'GIT_REPO_DIR', '/opt/edx/course_repos')
GIT_IMPORT_STATIC = getattr(settings, 'GIT_IMPORT_STATIC', True)


class CourseImportLog(mongoengine.Document):
    """Mongoengine model for git log"""
    # pylint: disable-msg=R0924

    course_id = mongoengine.StringField(max_length=128)
    location = mongoengine.StringField(max_length=168)
    import_log = mongoengine.StringField(max_length=20 * 65535)
    git_log = mongoengine.StringField(max_length=65535)
    repo_dir = mongoengine.StringField(max_length=128)
    created = mongoengine.DateTimeField()
    meta = {'indexes': ['course_id', 'created'],
            'allow_inheritance': False}


def add_repo(repo, rdir_in):
    """This will add a git repo into the mongo modulestore"""
    # pylint: disable-msg=R0915

    # Set defaults even if it isn't defined in settings
    mongo_db = {
        'host': 'localhost',
        'user': '',
        'password': '',
        'db': 'xlog',
    }

    # Allow overrides
    if hasattr(settings, 'MONGODB_LOG'):
        for config_item in ['host', 'user', 'password', 'db', ]:
            mongo_db[config_item] = settings.MONGODB_LOG.get(
                config_item, mongo_db[config_item])

    if not os.path.isdir(GIT_REPO_DIR):
        log.critical(_("Path {0} doesn't exist, please create it, or configure a "
                       "different path with GIT_REPO_DIR").format(GIT_REPO_DIR))
        return -1

    # -----------------------------------------------------------------------------
    # pull from git
    if not (repo.endswith('.git') or repo.startswith('http:') or
       repo.startswith('https:') or repo.startswith('git:')):

        log.error(_('Oops, not a git ssh url?'))
        log.error(_('Expecting something like git@github.com:mitocw/edx4edx_lite.git'))
        return -1

    if rdir_in:
        rdir = rdir_in
        rdir = os.path.basename(rdir)
    else:
        rdir = repo.rsplit('/', 1)[-1].rsplit('.git', 1)[0]

    log.debug('rdir = {0}'.format(rdir))

    rdirp = '{0}/{1}'.format(GIT_REPO_DIR, rdir)
    if os.path.exists(rdirp):
        log.info(_('directory already exists, doing a git pull instead of git clone'))
        cmd = 'cd {0}/{1}; git pull'.format(GIT_REPO_DIR, rdir)
    else:
        cmd = 'cd {0}; git clone "{1}"'.format(GIT_REPO_DIR, repo)

    log.debug(cmd)
    ret_git = os.popen(cmd).read()
    log.debug(ret_git)

    if not os.path.exists('{0}/{1}'.format(GIT_REPO_DIR, rdir)):
        log.error(_('git clone failed!'))
        return -1

    # get commit id
    commit_id = os.popen('cd {0}; git log -n 1 | head -1'.format(rdirp)).read().strip().split(' ')[1]

    ret_git += _('\nCommit ID: {0}').format(commit_id)

    # get branch
    branch = ''
    for k in os.popen('cd {0}; git branch'.format(rdirp)).readlines():
        if k[0] == '*':
            branch = k[2:].strip()

    ret_git += '   \nBranch: {0}'.format(branch)

    # Get XML logging logger and capture debug to parse results
    output = StringIO.StringIO()
    import_logger = logging.getLogger('xmodule.modulestore.xml_importer')
    import_log_handler = logging.StreamHandler(output)
    import_log_handler.setLevel(logging.DEBUG)
    import_logger.addHandler(import_log_handler)
    try:
        management.call_command('import', GIT_REPO_DIR, rdir,
                                nostatic=not GIT_IMPORT_STATIC)
    except CommandError, ex:
        log.critical(_('Unable to run import command.'))
        log.critical(_('Error was {0}').format(str(ex)))
        return -1

    ret_import = output.getvalue()

    course_id = 'unknown'
    location = 'unknown'

    # extract course ID from output of import-command-run and make symlink
    # this is needed in order for custom course scripts to work
    match = re.search('(?ms)===> IMPORTING course to location ([^ \n]+)',
                      ret_import)
    if match:
        location = match.group(1).strip()
        log.debug('location = {0}'.format(location))
        course_id = location.replace('i4x://', '').replace(
            '/course/', '/').split('\n')[0].strip()

        cdir = '{0}/{1}'.format(GIT_REPO_DIR, course_id.split('/')[1])
        log.debug(_('Studio course dir = {0}').format(cdir))

        if os.path.exists(cdir) and not os.path.islink(cdir):
            log.debug(_('   -> exists, but is not symlink'))
            log.debug(os.popen('ls -l {0}'.format(cdir)).read())
            log.debug(os.popen('rmdir {0}'.format(cdir)).read())

        if not os.path.exists(cdir):
            log.debug(_('   -> creating symlink'))
            log.debug(os.popen('ln -s {0} {1}'.format(rdirp,
                      cdir)).read())
            log.debug(os.popen('ls -l {0}'.format(cdir)).read())

    # -----------------------------------------------------------------------------
    # store import-command-run output in mongo
    mongouri = 'mongodb://{0}/{1}'.format(mongo_db['host'],
                                          mongo_db['db'])
    try:
        mdb = mongoengine.connect(mongo_db['db'], host=mongouri,
                                  username=mongo_db['user'],
                                  password=mongo_db['password'])
    except mongoengine.connection.ConnectionError, ex:
        log.critical(_('Unable to connect to mongodb to save log, please '
                       'check MONGODB_LOG settings'))
        log.critical(_('Error was: {0}').format(str(ex)))
        return -1
    logging.critical(mongoengine.connection.get_db())
    cil = CourseImportLog(
        course_id=course_id,
        location=location,
        repo_dir=rdir,
        created=datetime.datetime.now(),
        import_log=ret_import,
        git_log=ret_git,
    )
    cil.save()

    log.debug(_('saved CourseImportLog for {0}').format(cil.course_id))
    mdb.disconnect()
    return 0

if __name__ == '__main__':
    # pylint: disable-msg=C0103

    if len(sys.argv) < 2:
        print(_('This script requires at least one argument, the git URL'))
        sys.exit(1)

    if len(sys.argv) > 3:
        print(_('This script requires no more than two arguments.'))
        sys.exit(1)

    rdir_arg = None

    # check that we are using mongo modulestore
    if not 'mongo' in str(modulestore().__class__):
        print _('This script requires a mongo module store')
        sys.exit(1)

    if len(sys.argv) > 2:
        rdir_arg = sys.argv[2]

    if add_repo(sys.argv[1], rdir_arg) != 0:
        sys.exit(1)
