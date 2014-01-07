"""
Script for importing courseware from git/xml into a mongo modulestore
"""

import os
import re
import datetime
import StringIO
import subprocess
import logging

from django.conf import settings
from django.core import management
from django.core.management.base import BaseCommand, CommandError
from django.utils.translation import ugettext as _
import mongoengine

from dashboard.models import CourseImportLog
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.xml import XMLModuleStore

log = logging.getLogger(__name__)

GIT_REPO_DIR = getattr(settings, 'GIT_REPO_DIR', '/opt/edx/course_repos')
GIT_IMPORT_STATIC = getattr(settings, 'GIT_IMPORT_STATIC', True)

GIT_IMPORT_NO_DIR = -1
GIT_IMPORT_URL_BAD = -2
GIT_IMPORT_CANNOT_PULL = -3
GIT_IMPORT_XML_IMPORT_FAILED = -4
GIT_IMPORT_UNSUPPORTED_STORE = -5
GIT_IMPORT_MONGODB_FAIL = -6
GIT_IMPORT_BAD_REPO = -7


def add_repo(repo, rdir_in):
    """This will add a git repo into the mongo modulestore"""
    # pylint: disable=R0915

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
        log.critical(_("Path {0} doesn't exist, please create it, "
                       "or configure a different path with "
                       "GIT_REPO_DIR").format(GIT_REPO_DIR))
        return GIT_IMPORT_NO_DIR

    # pull from git
    if not repo.endswith('.git') or not (
            repo.startswith('http:') or
            repo.startswith('https:') or
            repo.startswith('git:') or
            repo.startswith('file:')):

        log.error(_('Oops, not a git ssh url?'))
        log.error(_('Expecting something like '
                    'git@github.com:mitocw/edx4edx_lite.git'))
        return GIT_IMPORT_URL_BAD

    if rdir_in:
        rdir = rdir_in
        rdir = os.path.basename(rdir)
    else:
        rdir = repo.rsplit('/', 1)[-1].rsplit('.git', 1)[0]

    log.debug('rdir = {0}'.format(rdir))

    rdirp = '{0}/{1}'.format(GIT_REPO_DIR, rdir)
    if os.path.exists(rdirp):
        log.info(_('directory already exists, doing a git pull instead '
                   'of git clone'))
        cmd = ['git', 'pull', ]
        cwd = '{0}/{1}'.format(GIT_REPO_DIR, rdir)
    else:
        cmd = ['git', 'clone', repo, ]
        cwd = GIT_REPO_DIR

    log.debug(cmd)
    cwd = os.path.abspath(cwd)
    try:
        ret_git = subprocess.check_output(cmd, cwd=cwd)
    except subprocess.CalledProcessError:
        log.exception(_('git clone or pull failed!'))
        return GIT_IMPORT_CANNOT_PULL
    log.debug(ret_git)

    # get commit id
    cmd = ['git', 'log', '-1', '--format=%H', ]
    try:
        commit_id = subprocess.check_output(cmd, cwd=rdirp)
    except subprocess.CalledProcessError:
        log.exception(_('Unable to get git log'))
        return GIT_IMPORT_BAD_REPO

    ret_git += _('\nCommit ID: {0}').format(commit_id)

    # get branch
    cmd = ['git', 'rev-parse', '--abbrev-ref', 'HEAD', ]
    try:
        branch = subprocess.check_output(cmd, cwd=rdirp)
    except subprocess.CalledProcessError:
        log.exception(_('Unable to get branch info'))
        return GIT_IMPORT_BAD_REPO

    ret_git += '   \nBranch: {0}'.format(branch)

    # Get XML logging logger and capture debug to parse results
    output = StringIO.StringIO()
    import_log_handler = logging.StreamHandler(output)
    import_log_handler.setLevel(logging.DEBUG)

    logger_names = ['xmodule.modulestore.xml_importer', 'git_add_course',
                    'xmodule.modulestore.xml', 'xmodule.seq_module', ]
    loggers = []

    for logger_name in logger_names:
        logger = logging.getLogger(logger_name)
        logger.old_level = logger.level
        logger.setLevel(logging.DEBUG)
        logger.addHandler(import_log_handler)
        loggers.append(logger)

    try:
        management.call_command('import', GIT_REPO_DIR, rdir,
                                nostatic=not GIT_IMPORT_STATIC)
    except CommandError:
        log.exception(_('Unable to run import command.'))
        return GIT_IMPORT_XML_IMPORT_FAILED
    except NotImplementedError:
        log.exception(_('The underlying module store does not support import.'))
        return GIT_IMPORT_UNSUPPORTED_STORE

    ret_import = output.getvalue()

    # Remove handler hijacks
    for logger in loggers:
        logger.setLevel(logger.old_level)
        logger.removeHandler(import_log_handler)

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
            log.debug(subprocess.check_output(['ls', '-l', ],
                                              cwd=os.path.abspath(cdir)))
            try:
                os.rmdir(os.path.abspath(cdir))
            except OSError:
                log.exception(_('Failed to remove course directory'))

        if not os.path.exists(cdir):
            log.debug(_('   -> creating symlink between {0} and {1}').format(rdirp, cdir))
            try:
                os.symlink(os.path.abspath(rdirp), os.path.abspath(cdir))
            except OSError:
                log.exception(_('Unable to create course symlink'))
            log.debug(subprocess.check_output(['ls', '-l', ],
                                              cwd=os.path.abspath(cdir)))

    # store import-command-run output in mongo
    mongouri = 'mongodb://{user}:{password}@{host}/{db}'.format(**mongo_db)

    try:
        if mongo_db['user'] and mongo_db['password']:
            mdb = mongoengine.connect(mongo_db['db'], host=mongouri)
        else:
            mdb = mongoengine.connect(mongo_db['db'], host=mongo_db['host'])
    except mongoengine.connection.ConnectionError:
        log.exception(_('Unable to connect to mongodb to save log, please '
                        'check MONGODB_LOG settings'))
        return GIT_IMPORT_MONGODB_FAIL
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


class Command(BaseCommand):
    """
    Pull a git repo and import into the mongo based content database.
    """

    help = _('Import the specified git repository into the '
             'modulestore and directory')

    def handle(self, *args, **options):
        """Check inputs and run the command"""

        if isinstance(modulestore, XMLModuleStore):
            raise CommandError(_('This script requires a mongo module store'))

        if len(args) < 1:
            raise CommandError(_('This script requires at least one argument, '
                                 'the git URL'))

        if len(args) > 2:
            raise CommandError(_('This script requires no more than two '
                                 'arguments'))

        rdir_arg = None

        if len(args) > 1:
            rdir_arg = args[1]

        if add_repo(args[0], rdir_arg) != 0:
            raise CommandError(_('Repo was not added, check log output '
                                 'for details'))
