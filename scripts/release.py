#!/usr/bin/env python
"""
a release-master multitool
"""
from __future__ import print_function, unicode_literals
import sys
from path import path
from git import Repo, Commit
from git.refs.symbolic import SymbolicReference
import argparse
from datetime import date, timedelta
from dateutil.parser import parse as parse_datestring
import re
from collections import OrderedDict, defaultdict
import textwrap
import requests

IGNORED_EMAILS = set(("vagrant@precise32.(none)",))
JIRA_RE = re.compile(r"\b[A-Z]{2,}-\d+\b")
PR_BRANCH_RE = re.compile(r"remotes/origin/pr/(\d+)")
PROJECT_ROOT = path(__file__).abspath().dirname()
repo = Repo(PROJECT_ROOT)
git = repo.git


def make_parser():
    parser = argparse.ArgumentParser(description="release master multitool")
    parser.add_argument(
        '--previous', '--prev', '-p', metavar="GITREV", default="origin/release",
        help="previous release [origin/release]")
    parser.add_argument(
        '--current', '--curr', '-c', metavar="GITREV", default="HEAD",
        help="current release candidate [HEAD]")
    parser.add_argument(
        '--date', '-d',
        help="expected release date: defaults to "
        "next Tuesday [{}]".format(default_release_date()))
    parser.add_argument(
        '--merge', '-m', action="store_true", default=False,
        help="include merge commits")
    parser.add_argument(
        '--table', '-t', action="store_true", default=False,
        help="only print table")
    parser.add_argument(
        '--commit-table', action="store_true", default=False,
        help="Display table by commit, instead of by PR")
    return parser


def ensure_pr_fetch():
    # it would be nice to use the git-python API to do this, but it doesn't seem
    # to support configurations with more than one value per key. :(
    origin_fetches = git.config("remote.origin.fetch", get_all=True).splitlines()
    pr_fetch = '+refs/pull/*/head:refs/remotes/origin/pr/*'
    if pr_fetch not in origin_fetches:
        git.config("remote.origin.fetch", pr_fetch, add=True)
        git.fetch()


def default_release_date():
    """
    Returns a date object corresponding to the expected date of the next release:
    normally, this Tuesday.
    """
    today = date.today()
    TUESDAY = 2
    days_until_tuesday = (TUESDAY - today.isoweekday()) % 7
    return today + timedelta(days=days_until_tuesday)


def parse_ticket_references(text):
    """
    Given a commit message, return a list of all JIRA ticket references in that
    message. If there are no ticket references, return an empty list.
    """
    return JIRA_RE.findall(text)


def emails(commit_range):
    """
    Returns a set of all email addresses responsible for the commits between
    the two commit references.
    """
    # %ae prints the authored_by email for the commit
    # %n prints a newline
    # %ce prints the committed_by email for the commit
    emails = set(git.log(commit_range, format='%ae%n%ce').splitlines())
    return emails - IGNORED_EMAILS


def commits_by_email(commit_range, include_merge=False):
    """
    Return a ordered dictionary of {email: commit_list}
    The dictionary is alphabetically ordered by email address
    The commit list is ordered by commit author date
    """
    kwargs = {}
    if not include_merge:
        kwargs["no-merges"] = True

    data = OrderedDict()
    for email in sorted(emails(commit_range)):
        authored_commits = set(repo.iter_commits(
            commit_range, author=email, **kwargs
        ))
        committed_commits = set(repo.iter_commits(
            commit_range, committer=email, **kwargs
        ))
        commits = authored_commits | committed_commits
        data[email] = sorted(commits, key=lambda c: c.authored_date)
    return data


class NotFoundError(Exception): pass


def get_pr_for_commit(commit, branch="master"):
    """
    http://stackoverflow.com/questions/8475448/find-merge-commit-which-include-a-specific-commit
    """
    remote_branch = git.describe(commit, all=True, contains=True)
    match = PR_BRANCH_RE.search(remote_branch)
    if match:
        pr_num = int(match.group(1))
        return pr_num
    # if `git describe` didn't work, we need to use `git branch` -- it's slower
    remote_branches = git.branch(commit, all=True, contains=True).splitlines()
    for remote_branch in remote_branches:
        remote_branch = remote_branch.strip()
        match = PR_BRANCH_RE.search(remote_branch)
        if match:
            pr_num = int(match.group(1))
            # we have a pull request -- but is it the right one?
            ref = SymbolicReference(repo, "refs/{}".format(remote_branch))
            merge_base = git.merge_base(ref, branch)
            rev = "{base}^..{branch}".format(base=merge_base, branch=remote_branch)
            pr_commits = list(Commit.iter_items(repo, rev))
            if commit in pr_commits:
                # found it!
                return pr_num
    err = NotFoundError(
        "Can't find pull request for commit {commit} against branch {branch}".format(
            commit=commit, branch=branch,
        )
    )
    err.commit = commit
    raise err


def get_merge_commit(commit, branch="master"):
    """
    Given a commit that was merged into the given branch, return the merge commit
    for that event.

    http://stackoverflow.com/questions/8475448/find-merge-commit-which-include-a-specific-commit
    """
    commit_range = "{}..{}".format(commit, branch)
    ancestry_paths = git.rev_list(commit_range, ancestry_path=True).splitlines()
    first_parents = git.rev_list(commit_range, first_parent=True).splitlines()
    both = set(ancestry_paths) & set(first_parents)
    for commit_hash in reversed(ancestry_paths):
        if commit_hash in both:
            return repo.commit(commit_hash)
    raise ValueError("No merge commit for {commit} in {branch}!".format(
        commit=commit, branch=branch,
    ))

def get_prs_for_commit_range(commit_range):
    """
    Returns a set of pull requests (integers) that contain all the commits
    in the given commit range.
    """
    pull_requests = set()
    for commit in Commit.iter_items(repo, commit_range):
        # ignore merge commits
        if len(commit.parents) > 1:
            continue
        pull_requests.add(get_pr_for_commit(commit))
    return pull_requests


def prs_by_email(commit_range):
    """
    Returns an ordered dictionary of {email: pr_list}
    Email is the email address of the person who merged the pull request
    The dictionary is alphabetically ordered by email address
    The pull request list is ordered by merge date
    """
    unordered_data = defaultdict(set)
    for pr_num in get_prs_for_commit_range(commit_range):
        ref = "refs/remotes/origin/pr/{num}".format(num=pr_num)
        branch = SymbolicReference(repo, ref)
        merge = get_merge_commit(branch.commit)
        unordered_data[merge.author.email].add((pr_num, merge))

    ordered_data = OrderedDict()
    for email in sorted(unordered_data.keys()):
        ordered = sorted(unordered_data[email], key=lambda pair: pair[1].authored_date)
        ordered_data[email] = [num for num, merge in ordered]
    return ordered_data


def generate_table_by_commit(commit_range, include_merge=False):
    """
    Return a string corresponding to a commit table to embed in Confluence
    """
    header = "||Author||Summary||Commit||JIRA||Verified?||"
    commit_link = "[commit|https://github.com/edx/edx-platform/commit/{sha}]"
    rows = [header]
    cbe = commits_by_email(commit_range, include_merge)
    for email, commits in cbe.items():
        for i, commit in enumerate(commits):
            rows.append("| {author} | {summary} | {commit} | {jira} | {verified} |".format(
                author=email if i == 0 else "",
                summary=commit.summary.replace("|", "\|"),
                commit=commit_link.format(sha=commit.hexsha),
                jira=", ".join(parse_ticket_references(commit.message)),
                verified="",
            ))
    return "\n".join(rows)


def get_pr_info(num):
    """
    Returns the info from the Github API
    """
    url = "https://api.github.com/repos/edx/edx-platform/pulls/{num}".format(num=num)
    response = requests.get(url)
    result = response.json()
    if not response.ok:
        raise requests.exceptions.RequestException(result["message"])
    return result


def generate_table_by_pr(commit_range):
    """
    Return a string corresponding to a commit table to embed in Confluence
    """
    header = "|| Merged By || Title || PR || JIRA || Verified? ||"
    pr_link = "[#{num}|https://github.com/edx/edx-platform/pull/{num}]"
    rows = [header]
    prbe = prs_by_email(commit_range)
    for email, pull_requests in prbe.items():
        for i, pull_request in enumerate(pull_requests):
            try:
                pr_info = get_pr_info(pull_request)
                title = pr_info["title"] or ""
                body = pr_info["body"] or ""
            except requests.exceptions.RequestException as e:
                print(
                    "Warning: could not fetch data for #{num}: {message}".format(
                        num=pull_request, message=e.message
                    ),
                    file=sys.stderr,
                )
                title = "?"
                body = "?"
            rows.append("| {merged_by} | {title} | {pull_request} | {jira} | {verified} |".format(
                merged_by=email if i == 0 else "",
                title=title.replace("|", "\|"),
                pull_request=pr_link.format(num=pull_request),
                jira=", ".join(parse_ticket_references(body)),
                verified="",
            ))
    return "\n".join(rows)


def generate_email(commit_range, release_date=None):
    """
    Returns a string roughly approximating an email.
    """
    if release_date is None:
        release_date = default_release_date()

    email = """
        To: {emails}

        You've made changes that are about to be released. All of the commits
        that you either authored or committed are listed below. Please verify them on
        stage.edx.org and stage-edge.edx.org.

        Please record your notes on https://edx-wiki.atlassian.net/wiki/display/ENG/Release+Page%3A+{date}
        and add any bugs found to the Release Candidate Bugs section.

        If you are a non-affiliated open-source contributor to edx-platform,
        the edX employee who merged in your pull request will manually verify
        your change(s), and you may disregard this message.
    """.format(
        emails=", ".join(sorted(emails(commit_range))),
        date=release_date.isoformat(),
    )
    return textwrap.dedent(email).strip()


def main():
    parser = make_parser()
    args = parser.parse_args()
    if isinstance(args.date, basestring):
        # user passed in a custom date, so we need to parse it
        args.date = parse_datestring(args.date).date()
    commit_range = "{0}..{1}".format(args.previous, args.current)

    if args.table:
        if args.commit_table:
            print(generate_table_by_commit(commit_range, include_merge=args.merge))
        else:
            print(generate_table_by_pr(commit_range))
        return

    print("EMAIL:")
    print(generate_email(commit_range, release_date=args.date).encode('UTF-8'))
    print("\n")
    print("Wiki Table:")
    print(
        "Type Ctrl+Shift+D on Confluence to embed the following table "
        "in your release wiki page"
    )
    print("\n")
    if args.commit_table:
        print(generate_table_by_commit(commit_range, include_merge=args.merge))
    else:
        print(generate_table_by_pr(commit_range))

if __name__ == "__main__":
    main()
