import logging
import os

from django.conf import settings
from fs.osfs import OSFS
from git import Repo, PushInfo

from xmodule.modulestore.xml_importer import import_from_xml
from xmodule.modulestore.django import modulestore
from collections import namedtuple

from .exceptions import GithubSyncError, InvalidRepo

log = logging.getLogger(__name__)

RepoSettings = namedtuple('RepoSettings', 'path branch origin')


def sync_all_with_github():
    """
    Sync all defined repositories from github
    """
    for repo_name in settings.REPOS:
        sync_with_github(load_repo_settings(repo_name))


def sync_with_github(repo_settings):
    """
    Sync specified repository from github

    repo_settings: A RepoSettings defining which repo to sync
    """
    revision, course = import_from_github(repo_settings)
    export_to_github(course, "Changes from cms import of revision %s" % revision, "CMS <cms@edx.org>")


def setup_repo(repo_settings):
    """
    Reset the local github repo specified by repo_settings

    repo_settings (RepoSettings): The settings for the repo to reset
    """
    course_dir = repo_settings.path
    repo_path = settings.GITHUB_REPO_ROOT / course_dir

    if not os.path.isdir(repo_path):
        Repo.clone_from(repo_settings.origin, repo_path)

    git_repo = Repo(repo_path)
    origin = git_repo.remotes.origin
    origin.fetch()

    # Do a hard reset to the remote branch so that we have a clean import
    git_repo.git.checkout(repo_settings.branch)

    return git_repo


def load_repo_settings(course_dir):
    """
    Returns the repo_settings for the course stored in course_dir
    """
    if course_dir not in settings.REPOS:
        raise InvalidRepo(course_dir)

    return RepoSettings(course_dir, **settings.REPOS[course_dir])


def import_from_github(repo_settings):
    """
    Imports data into the modulestore based on the XML stored on github
    """
    course_dir = repo_settings.path
    git_repo = setup_repo(repo_settings)
    git_repo.head.reset('origin/%s' % repo_settings.branch, index=True, working_tree=True)

    module_store = import_from_xml(modulestore(),
                                   settings.GITHUB_REPO_ROOT, course_dirs=[course_dir])
    return git_repo.head.commit.hexsha, module_store.courses[course_dir]


def export_to_github(course, commit_message, author_str=None):
    '''
    Commit any changes to the specified course with given commit message,
    and push to github (if MITX_FEATURES['GITHUB_PUSH'] is True).
    If author_str is specified, uses it in the commit.
    '''
    course_dir = course.metadata.get('data_dir', course.location.course)
    try:
        repo_settings = load_repo_settings(course_dir)
    except InvalidRepo:
        log.warning("Invalid repo {0}, not exporting data to xml".format(course_dir))
        return

    git_repo = setup_repo(repo_settings)

    fs = OSFS(git_repo.working_dir)
    xml = course.export_to_xml(fs)

    with fs.open('course.xml', 'w') as course_xml:
        course_xml.write(xml)

    if git_repo.is_dirty():
        git_repo.git.add(A=True)
        if author_str is not None:
            git_repo.git.commit(m=commit_message, author=author_str)
        else:
            git_repo.git.commit(m=commit_message)

        origin = git_repo.remotes.origin
        if settings.MITX_FEATURES['GITHUB_PUSH']:
            push_infos = origin.push()
            if len(push_infos) > 1:
                log.error('Unexpectedly pushed multiple heads: {infos}'.format(
                    infos="\n".join(str(info.summary) for info in push_infos)
                ))

            if push_infos[0].flags & PushInfo.ERROR:
                log.error('Failed push: flags={p.flags}, local_ref={p.local_ref}, '
                          'remote_ref_string={p.remote_ref_string}, '
                          'remote_ref={p.remote_ref}, old_commit={p.old_commit}, '
                          'summary={p.summary})'.format(p=push_infos[0]))
                raise GithubSyncError('Failed to push: {info}'.format(
                    info=str(push_infos[0].summary)
                ))
