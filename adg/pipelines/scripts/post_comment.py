"""
Python script file for posting coverage report as comment on Github PR
"""
# !/usr/bin/env python3
import argparse
import os

import requests

parser = argparse.ArgumentParser()
parser.add_argument('--type', '-t', help='Report type i.e. ADG, Edx')
parser.add_argument('--status', '-s', help='Test coverage status; 0 of cover is a success')
args = parser.parse_args()

CIRCLE_PULL_REQUEST = os.environ['CIRCLE_PULL_REQUEST']
GITHUB_BOT_TOKEN = os.environ['GITHUB_BOT_TOKEN']
CIRCLE_PROJECT_USERNAME = os.environ['CIRCLE_PROJECT_USERNAME']
CIRCLE_PROJECT_REPONAME = os.environ['CIRCLE_PROJECT_REPONAME']
CIRCLE_BUILD_NUM = os.environ['CIRCLE_BUILD_NUM']


def post_coverage_stats():
    """
    Post coverage stats to PR as a comment.

    Returns:
        None
    """
    diff_cover_report = os.environ.get('DIFF_COVER_REPORT')

    if not diff_cover_report:
        return

    print('Posting coverage report on PR')
    report_message = '## Diff Coverage Report {type}\nCheck-out complete **[report]({link})**.'.format(
        link=_artifacts_link(),
        type='- {}'.format(args.type) if args.type else '',
    )
    message = '{report_message} Coverage !!! {icon}\n```\n{report_stats}\n```'.format(
        report_message=report_message,
        report_stats=diff_cover_report,
        icon=':rocket:' if args.status == '0' else ':scream:',
    )

    _create_comment_on_pr(message)


def _artifacts_link():
    """
    Create complete URL for circleci artifacts

    Returns:
        String URL for circleci artifacts
    """
    circleci = 'https://app.circleci.com/pipelines'
    return '{root}/github/{username}/{repo}/{build}/workflows/workflows_id/jobs/{build}/artifacts'.format(
        root=circleci,
        username=CIRCLE_PROJECT_USERNAME,
        repo=CIRCLE_PROJECT_REPONAME,
        build=CIRCLE_BUILD_NUM,
    )


def _create_comment_on_pr(message):
    """
    Post comment on PR using Github api
    Args:
        message (str): Coverage Report or comment

    Returns:
        None
    """
    pr_number = CIRCLE_PULL_REQUEST.split('/')[-1]
    url = 'https://api.github.com/repos/{username}/{repo}/issues/{pr}/comments'.format(
        pr=pr_number,
        username=CIRCLE_PROJECT_USERNAME,
        repo=CIRCLE_PROJECT_REPONAME,
    )
    headers = {'Authorization': 'token {token}'.format(token=GITHUB_BOT_TOKEN)}
    response = requests.post(url, json={'body': message}, headers=headers)
    print('Comment status: ', response.status_code, response.reason)


post_coverage_stats()
