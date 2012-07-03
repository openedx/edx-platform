from git import Repo
from contentstore import import_from_xml
from fs.osfs import OSFS
import os
from xmodule.modulestore import Location
from django.conf import settings


def import_from_github(repo_settings):
    """
    Imports data into the modulestore based on the XML stored on github

    repo_settings is a dictionary with the following keys:
        path: file system path to the local git repo
        branch: name of the branch to track on github
        org: name of the 
    """
    repo_path = repo_settings['path']

    if not os.path.isdir(repo_path):
        Repo.clone_from(repo_settings['origin'], repo_path)

    git_repo = Repo(repo_path)
    origin = git_repo.remotes.origin
    origin.fetch()

    # Do a hard reset to the remote branch so that we have a clean import
    git_repo.git.checkout(repo_settings['branch'])
    git_repo.head.reset('origin/%s' % repo_settings['branch'], index=True, working_tree=True)

    return git_repo.head.commit.hexsha, import_from_xml(repo_settings['org'], repo_settings['course'], repo_path)


def repo_path_from_location(location):
    location = Location(location)
    for name, repo in settings.REPOS.items():
        if repo['org'] == location.org and repo['course'] == location.course:
            return repo['path']


def export_to_github(course, repo_path, commit_message):
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
            origin.push()
