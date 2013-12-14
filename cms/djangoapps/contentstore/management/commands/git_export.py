"""
This command exports a course from CMS to a git repository.
It takes as arguments the course id to export (i.e MITx/999/2020 ) and
the repository to commit too.  It takes username as an option for identifying
the commit, as well as a directory path to place the git repository.

By default it will use settings.GIT_REPO_EXPORT_DIR/repo_name as the cloned
directory.  It is branch aware, but will reset all local changes to the
repository before attempting to export the XML, add, and commit changes if
any have taken place.

This functionality is also available as an export view in studio if the giturl
attribute is set and the FEATURE['ENABLE_PUSH_TO_LMS'] is set.
"""

import logging
from optparse import make_option
import os
import subprocess
from urlparse import urlparse

from django.conf import settings
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.utils.translation import ugettext as _

from xmodule.contentstore.django import contentstore
from xmodule.course_module import CourseDescriptor
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.xml_exporter import export_to_xml

log = logging.getLogger(__name__)

GIT_REPO_EXPORT_DIR = getattr(settings, 'GIT_REPO_EXPORT_DIR',
                              '/edx/var/edxapp/export_course_repos')
GIT_EXPORT_DEFAULT_IDENT = getattr(settings, 'GIT_EXPORT_DEFAULT_IDENT',
                                   {'name': 'STUDIO_PUSH_TO_LMS',
                                    'email': 'STUDIO_PUSH_TO_LMS@example.com'})


class GitExportError(Exception):
    """
    Convenience exception class for git export error conditions.
    """

    NO_EXPORT_DIR = _("Path {0} doesn't exist, please create it, "
                      "or configure a different path with "
                      "GIT_REPO_EXPORT_DIR").format(GIT_REPO_EXPORT_DIR)
    URL_BAD = _('Non writable git url provided. Expecting something like:'
                ' git@github.com:mitocw/edx4edx_lite.git')
    URL_NO_AUTH = _('If using http urls, you must provide the username '
                    'and password in the url. Similar to '
                    'https://user:pass@github.com/user/course.')
    DETACHED_HEAD = _('Unable to determine branch, repo in detached HEAD mode')
    CANNOT_PULL = _('Unable to update or clone git repository.')
    XML_EXPORT_FAIL = _('Unable to export course to xml.')
    CANNOT_COMMIT = _('Unable to commit or push changes.')
    BAD_COURSE = _('Bad course location provided')
    MISSING_BRANCH = _('Missing branch on fresh clone')


def cmd_log(cmd, cwd):
    """
    Helper function to redirect stderr to stdout and log the command
    used along with the output. Will raise subprocess.CalledProcessError if
    command doesn't return 0, and returns the command's output.
    """
    output = subprocess.check_output(cmd, cwd=cwd, stderr=subprocess.STDOUT)
    log.debug(_('Command was: {0!r}. '
                'Working directory was: {1!r}').format(' '.join(cmd), cwd))
    log.debug(_('Command output was: {0!r}'.format(output)))
    return output


def export_to_git(course_loc, repo, user='', rdir=None):
    """Export a course to git."""
    # pylint: disable=R0915

    if course_loc.startswith('i4x://'):
        course_loc = course_loc[6:]

    if not os.path.isdir(GIT_REPO_EXPORT_DIR):
        raise GitExportError(GitExportError.NO_EXPORT_DIR)

    # Check for valid writable git url
    if not (repo.endswith('.git') or
            repo.startswith(('http:', 'https:', 'file:'))):
        raise GitExportError(GitExportError.URL_BAD)

    # Check for username and password if using http[s]
    if repo.startswith('http:') or repo.startswith('https:'):
        parsed = urlparse(repo)
        if parsed.username is None or parsed.password is None:
            raise GitExportError(GitExportError.URL_NO_AUTH)
    if rdir:
        rdir = os.path.basename(rdir)
    else:
        rdir = repo.rsplit('/', 1)[-1].rsplit('.git', 1)[0]

    log.debug("rdir = %s", rdir)

    # Pull or clone repo before exporting to xml
    # and update url in case origin changed.
    rdirp = '{0}/{1}'.format(GIT_REPO_EXPORT_DIR, rdir)
    branch = None
    if os.path.exists(rdirp):
        log.info(_('Directory already exists, doing a git reset and pull '
                   'instead of git clone.'))
        cwd = rdirp
        # Get current branch
        cmd = ['git', 'symbolic-ref', '--short', 'HEAD', ]
        try:
            branch = cmd_log(cmd, cwd).strip('\n')
        except subprocess.CalledProcessError as ex:
            log.exception('Failed to get branch: %r', ex.output)
            raise GitExportError(GitExportError.DETACHED_HEAD)

        cmds = [
            ['git', 'remote', 'set-url', 'origin', repo, ],
            ['git', 'fetch', 'origin', ],
            ['git', 'reset', '--hard', 'origin/{0}'.format(branch), ],
            ['git', 'pull', ],
        ]
    else:
        cmds = [['git', 'clone', repo, ], ]
        cwd = GIT_REPO_EXPORT_DIR

    cwd = os.path.abspath(cwd)
    for cmd in cmds:
        try:
            cmd_log(cmd, cwd)
        except subprocess.CalledProcessError as ex:
            log.exception('Failed to pull git repository: %r', ex.output)
            raise GitExportError(GitExportError.CANNOT_PULL)

    # export course as xml before commiting and pushing
    try:
        location = CourseDescriptor.id_to_location(course_loc)
    except ValueError:
        raise GitExportError(GitExportError.BAD_COURSE)

    root_dir = os.path.dirname(rdirp)
    course_dir = os.path.splitext(os.path.basename(rdirp))[0]
    try:
        export_to_xml(modulestore('direct'), contentstore(), location,
                      root_dir, course_dir, modulestore())
    except (EnvironmentError, AttributeError):
        log.exception('Failed export to xml')
        raise GitExportError(GitExportError.XML_EXPORT_FAIL)

    # Get current branch if not already set
    if not branch:
        cmd = ['git', 'symbolic-ref', '--short', 'HEAD', ]
        try:
            branch = cmd_log(cmd, os.path.abspath(rdirp)).strip('\n')
        except subprocess.CalledProcessError as ex:
            log.exception('Failed to get branch from freshly cloned repo: %r',
                          ex.output)
            raise GitExportError(GitExportError.MISSING_BRANCH)

    # Now that we have fresh xml exported, set identity, add
    # everything to git, commit, and push to the right branch.
    ident = {}
    try:
        user = User.objects.get(username=user)
        ident['name'] = user.username
        ident['email'] = user.email
    except User.DoesNotExist:
        # That's ok, just use default ident
        ident = GIT_EXPORT_DEFAULT_IDENT
    time_stamp = timezone.now()
    cwd = os.path.abspath(rdirp)
    commit_msg = 'Export from Studio at {1}'.format(user, time_stamp)
    try:
        cmd_log(['git', 'config', 'user.email', ident['email'], ], cwd)
        cmd_log(['git', 'config', 'user.name', ident['name'], ], cwd)
        cmd_log(['git', 'add', '.'], cwd)
        cmd_log(['git', 'commit', '-a', '-m', commit_msg], cwd)
        cmd_log(['git', 'push', '-q', 'origin', branch], cwd)
    except subprocess.CalledProcessError as ex:
        log.exception('Error running git push commands: %r', ex.output)
        raise GitExportError(GitExportError.CANNOT_COMMIT)


class Command(BaseCommand):
    """
    Take a course from studio and export it to a git repository.
    """

    option_list = BaseCommand.option_list + (
        make_option('--user', '-u', dest='user',
                    help='Add a user to the commit message.'),
        make_option('--repo_dir', '-r', dest='repo',
                    help='Specify existing git repo directory.'),
    )

    help = _('Take the specified course and attempt to '
             'export it to a git repository\n. Course directory '
             'must already be a git repository. Usage: '
             ' git_export <course_loc> <git_url>')

    def handle(self, *args, **options):
        """
        Checks arguments and runs export function if they are good
        """

        if len(args) != 2:
            raise CommandError(_('This script requires exactly two arguments: '
                                 'course_loc and git_url'))

        # Rethrow GitExportError as CommandError for SystemExit
        try:
            export_to_git(
                args[0],
                args[1],
                options.get('user', ''),
                options.get('rdir', None)
            )
        except GitExportError as ex:
            raise CommandError(str(ex))
