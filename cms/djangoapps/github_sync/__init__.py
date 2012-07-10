import logging
import os

from django.conf import settings
from fs.osfs import OSFS
from git import Repo, PushInfo

from contentstore import import_from_xml
from xmodule.modulestore import Location

from .exceptions import GithubSyncError

log = logging.getLogger(__name__)


def import_from_github(repo_settings):
    """
    Imports data into the modulestore based on the XML stored on github

    repo_settings is a dictionary with the following keys:
        path: file system path to the local git repo
        branch: name of the branch to track on github
    """
    repo_path = repo_settings['path']
    data_dir, course_dir = os.path.split(repo_path)

    if not os.path.isdir(repo_path):
        Repo.clone_from(repo_settings['origin'], repo_path)

    git_repo = Repo(repo_path)
    origin = git_repo.remotes.origin
    origin.fetch()

    # Do a hard reset to the remote branch so that we have a clean import
    git_repo.git.checkout(repo_settings['branch'])
    git_repo.head.reset('origin/%s' % repo_settings['branch'], index=True, working_tree=True)
    module_store = import_from_xml(data_dir, course_dirs=[course_dir])
    return git_repo.head.commit.hexsha, module_store.courses[course_dir]


def export_to_github(course, commit_message):
    repo_path = settings.DATA_DIR / course.metadata.get('course_dir', course.location.course)
    fs = OSFS(repo_path)
    xml = course.export_to_xml(fs)

    with fs.open('course.xml', 'w') as course_xml:
        course_xml.write(xml)

    git_repo = Repo(repo_path)
    if git_repo.is_dirty():
        git_repo.git.add(A=True)
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
