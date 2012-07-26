import logging
import json

from django.http import HttpResponse
from django.conf import settings
from django_future.csrf import csrf_exempt

from . import sync_with_github, load_repo_settings

log = logging.getLogger()


@csrf_exempt
def github_post_receive(request):
    """
    This view recieves post-receive requests from github whenever one of
    the watched repositiories changes.

    It is responsible for updating the relevant local git repo,
    importing the new version of the course (if anything changed),
    and then pushing back to github any changes that happened as part of the
    import.

    The github request format is described here: https://help.github.com/articles/post-receive-hooks
    """

    payload = json.loads(request.POST['payload'])

    ref = payload['ref']

    if not ref.startswith('refs/heads/'):
        log.info('Ignore changes to non-branch ref %s' % ref)
        return HttpResponse('Ignoring non-branch')

    branch_name = ref.replace('refs/heads/', '', 1)

    repo_name = payload['repository']['name']

    if repo_name not in settings.REPOS:
        log.info('No repository matching %s found' % repo_name)
        return HttpResponse('No Repo Found')

    repo = load_repo_settings(repo_name)

    if repo.branch != branch_name:
        log.info('Ignoring changes to non-tracked branch %s in repo %s' % (branch_name, repo_name))
        return HttpResponse('Ignoring non-tracked branch')

    sync_with_github(repo)

    return HttpResponse('Push received')
