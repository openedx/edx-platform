"""
Provides a function for importing a git repository into the lms
instance when using a mongo modulestore
"""

import os
import re
import StringIO
import subprocess
import logging

from django.conf import settings
from django.core import management
from django.core.management.base import CommandError
from django.utils import timezone
from django.utils.translation import ugettext as _
import mongoengine

from dashboard.models import CourseImportLog
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey
from opaque_keys.edx.locations import SlashSeparatedCourseKey

log = logging.getLogger(__name__)

GIT_REPO_DIR = getattr(settings, 'GIT_REPO_DIR', '/edx/var/app/edxapp/course_repos')
GIT_IMPORT_STATIC = getattr(settings, 'GIT_IMPORT_STATIC', True)


class GitImportError(Exception):
    """
    Exception class for handling the typical errors in a git import.
    """

    NO_DIR = _("Path {0} doesn't exist, please create it, "
               "or configure a different path with "
               "GIT_REPO_DIR").format(GIT_REPO_DIR)
    URL_BAD = _('Non usable git url provided. Expecting something like:'
                ' git@github.com:mitocw/edx4edx_lite.git')
    BAD_REPO = _('Unable to get git log')
    CANNOT_PULL = _('git clone or pull failed!')
    XML_IMPORT_FAILED = _('Unable to run import command.')
    UNSUPPORTED_STORE = _('The underlying module store does not support import.')
    # Translators: This is an error message when they ask for a
    # particular version of a git repository and that version isn't
    # available from the remote source they specified
    REMOTE_BRANCH_MISSING = _('The specified remote branch is not available.')
    # Translators: Error message shown when they have asked for a git
    # repository branch, a specific version within a repository, that
    # doesn't exist, or there is a problem changing to it.
    CANNOT_BRANCH = _('Unable to switch to specified branch. Please check '
                      'your branch name.')


def cmd_log(cmd, cwd):
    """
    Helper function to redirect stderr to stdout and log the command
    used along with the output. Will raise subprocess.CalledProcessError if
    command doesn't return 0, and returns the command's output.
    """
    output = subprocess.check_output(cmd, cwd=cwd, stderr=subprocess.STDOUT)

    log.debug(u'Command was: %r. Working directory was: %r', ' '.join(cmd), cwd)
    log.debug(u'Command output was: %r', output)
    return output


def switch_branch(branch, rdir):
    """
    This will determine how to change the branch of the repo, and then
    use the appropriate git commands to do so.

    Raises an appropriate GitImportError exception if there is any issues with changing
    branches.
    """
    # Get the latest remote
    try:
        cmd_log(['git', 'fetch', ], rdir)
    except subprocess.CalledProcessError as ex:
        log.exception('Unable to fetch remote: %r', ex.output)
        raise GitImportError(GitImportError.CANNOT_BRANCH)

    # Check if the branch is available from the remote.
    cmd = ['git', 'ls-remote', 'origin', '-h', 'refs/heads/{0}'.format(branch), ]
    try:
        output = cmd_log(cmd, rdir)
    except subprocess.CalledProcessError as ex:
        log.exception('Getting a list of remote branches failed: %r', ex.output)
        raise GitImportError(GitImportError.CANNOT_BRANCH)
    if branch not in output:
        raise GitImportError(GitImportError.REMOTE_BRANCH_MISSING)
    # Check it the remote branch has already been made locally
    cmd = ['git', 'branch', '-a', ]
    try:
        output = cmd_log(cmd, rdir)
    except subprocess.CalledProcessError as ex:
        log.exception('Getting a list of local branches failed: %r', ex.output)
        raise GitImportError(GitImportError.CANNOT_BRANCH)
    branches = []
    for line in output.split('\n'):
        branches.append(line.replace('*', '').strip())

    if branch not in branches:
        # Checkout with -b since it is remote only
        cmd = ['git', 'checkout', '--force', '--track',
               '-b', branch, 'origin/{0}'.format(branch), ]
        try:
            cmd_log(cmd, rdir)
        except subprocess.CalledProcessError as ex:
            log.exception('Unable to checkout remote branch: %r', ex.output)
            raise GitImportError(GitImportError.CANNOT_BRANCH)
    # Go ahead and reset hard to the newest version of the branch now that we know
    # it is local.
    try:
        cmd_log(['git', 'reset', '--hard', 'origin/{0}'.format(branch), ], rdir)
    except subprocess.CalledProcessError as ex:
        log.exception('Unable to reset to branch: %r', ex.output)
        raise GitImportError(GitImportError.CANNOT_BRANCH)


def add_repo(repo, rdir_in, branch=None):
    """
    This will add a git repo into the mongo modulestore.
    If branch is left as None, it will fetch the most recent
    version of the current branch.
    """
    # pylint: disable=too-many-statements

    # Set defaults even if it isn't defined in settings
    mongo_db = {
        'host': 'localhost',
        'port': 27017,
        'user': '',
        'password': '',
        'db': 'xlog',
    }

    # Allow overrides
    if hasattr(settings, 'MONGODB_LOG'):
        for config_item in ['host', 'user', 'password', 'db', 'port']:
            mongo_db[config_item] = settings.MONGODB_LOG.get(
                config_item, mongo_db[config_item])

    if not os.path.isdir(GIT_REPO_DIR):
        raise GitImportError(GitImportError.NO_DIR)
    # pull from git
    if not (repo.endswith('.git') or
            repo.startswith(('http:', 'https:', 'git:', 'file:'))):
        raise GitImportError(GitImportError.URL_BAD)

    if rdir_in:
        rdir = os.path.basename(rdir_in)
    else:
        rdir = repo.rsplit('/', 1)[-1].rsplit('.git', 1)[0]
    log.debug('rdir = %s', rdir)

    rdirp = '{0}/{1}'.format(GIT_REPO_DIR, rdir)
    if os.path.exists(rdirp):
        log.info('directory already exists, doing a git pull instead '
                 'of git clone')
        cmd = ['git', 'pull', ]
        cwd = rdirp
    else:
        cmd = ['git', 'clone', repo, ]
        cwd = GIT_REPO_DIR

    cwd = os.path.abspath(cwd)
    try:
        ret_git = cmd_log(cmd, cwd=cwd)
    except subprocess.CalledProcessError as ex:
        log.exception('Error running git pull: %r', ex.output)
        raise GitImportError(GitImportError.CANNOT_PULL)

    if branch:
        switch_branch(branch, rdirp)

    # get commit id
    cmd = ['git', 'log', '-1', '--format=%H', ]
    try:
        commit_id = cmd_log(cmd, cwd=rdirp)
    except subprocess.CalledProcessError as ex:
        log.exception('Unable to get git log: %r', ex.output)
        raise GitImportError(GitImportError.BAD_REPO)

    ret_git += '\nCommit ID: {0}'.format(commit_id)

    # get branch
    cmd = ['git', 'symbolic-ref', '--short', 'HEAD', ]
    try:
        branch = cmd_log(cmd, cwd=rdirp)
    except subprocess.CalledProcessError as ex:
        # I can't discover a way to excercise this, but git is complex
        # so still logging and raising here in case.
        log.exception('Unable to determine branch: %r', ex.output)
        raise GitImportError(GitImportError.BAD_REPO)

    ret_git += '{0}Branch: {1}'.format('   \n', branch)

    # Get XML logging logger and capture debug to parse results
    output = StringIO.StringIO()
    import_log_handler = logging.StreamHandler(output)
    import_log_handler.setLevel(logging.DEBUG)

    logger_names = ['xmodule.modulestore.xml_importer', 'git_add_course',
                    'xmodule.modulestore.xml', 'xmodule.seq_module', ]
    loggers = []

    for logger_name in logger_names:
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.DEBUG)
        logger.addHandler(import_log_handler)
        loggers.append(logger)

    try:
        management.call_command('import', GIT_REPO_DIR, rdir,
                                nostatic=not GIT_IMPORT_STATIC)
    except CommandError:
        raise GitImportError(GitImportError.XML_IMPORT_FAILED)
    except NotImplementedError:
        raise GitImportError(GitImportError.UNSUPPORTED_STORE)

    ret_import = output.getvalue()

    # Remove handler hijacks
    for logger in loggers:
        logger.setLevel(logging.NOTSET)
        logger.removeHandler(import_log_handler)

    course_key = None
    location = 'unknown'

    # extract course ID from output of import-command-run and make symlink
    # this is needed in order for custom course scripts to work
    match = re.search(r'(?ms)===> IMPORTING courselike (\S+)', ret_import)
    if match:
        course_id = match.group(1)
        try:
            course_key = CourseKey.from_string(course_id)
        except InvalidKeyError:
            course_key = SlashSeparatedCourseKey.from_deprecated_string(course_id)
        cdir = '{0}/{1}'.format(GIT_REPO_DIR, course_key.course)
        log.debug('Studio course dir = %s', cdir)

        if os.path.exists(cdir) and not os.path.islink(cdir):
            log.debug('   -> exists, but is not symlink')
            log.debug(subprocess.check_output(['ls', '-l', ],
                                              cwd=os.path.abspath(cdir)))
            try:
                os.rmdir(os.path.abspath(cdir))
            except OSError:
                log.exception('Failed to remove course directory')

        if not os.path.exists(cdir):
            log.debug('   -> creating symlink between %s and %s', rdirp, cdir)
            try:
                os.symlink(os.path.abspath(rdirp), os.path.abspath(cdir))
            except OSError:
                log.exception('Unable to create course symlink')
            log.debug(subprocess.check_output(['ls', '-l', ],
                                              cwd=os.path.abspath(cdir)))

    # store import-command-run output in mongo
    mongouri = 'mongodb://{user}:{password}@{host}:{port}/{db}'.format(**mongo_db)

    try:
        if mongo_db['user'] and mongo_db['password']:
            mdb = mongoengine.connect(mongo_db['db'], host=mongouri)
        else:
            mdb = mongoengine.connect(mongo_db['db'], host=mongo_db['host'], port=mongo_db['port'])
    except mongoengine.connection.ConnectionError:
        log.exception('Unable to connect to mongodb to save log, please '
                      'check MONGODB_LOG settings')
    cil = CourseImportLog(
        course_id=course_key,
        location=location,
        repo_dir=rdir,
        created=timezone.now(),
        import_log=ret_import,
        git_log=ret_git,
    )
    cil.save()

    log.debug('saved CourseImportLog for %s', cil.course_id)
    mdb.disconnect()
