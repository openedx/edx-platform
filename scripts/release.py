#!/usr/bin/env python
"""
a release-master multitool
"""
from path import path
from git import Repo
import argparse
from datetime import date, timedelta
from dateutil.parser import parse as parse_datestring
import re
from collections import OrderedDict
import textwrap

JIRA_RE = re.compile(r"\b[A-Z]{2,}-\d+\b")
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
    return parser


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


def emails(from_commit, to_commit):
    """
    Returns a set of all email addresses responsible for the commits between
    the two commit references.
    """
    # %ae prints the authored_by email for the commit
    # %n prints a newline
    # %ce prints the committed_by email for the commit
    return set(git.log(from_commit, to_commit, format='%ae%n%ce').splitlines())


def commits_by_email(from_commit, to_commit, include_merge=False):
    """
    Return a ordered dictionary of {email: commit_list}
    The dictionary is alphabetically ordered by email address
    The commit list is ordered by commit author date
    """
    kwargs = {}
    if not include_merge:
        kwargs["no-merges"] = True
    commit_range = "{0}..{1}".format(from_commit, to_commit)

    data = OrderedDict()
    for email in sorted(emails(from_commit, to_commit)):
        authored_commits = set(repo.iter_commits(
            commit_range, author=email, **kwargs
        ))
        committed_commits = set(repo.iter_commits(
            commit_range, committer=email, **kwargs
        ))
        commits = authored_commits | committed_commits
        data[email] = sorted(commits, key=lambda c: c.authored_date)
    return data


def generate_table(from_commit, to_commit, include_merge=False):
    """
    Return a string corresponding to a commit table to embed in Confluence
    """
    header = "||Author||Summary||Commit||JIRA||Verified?||"
    commit_link = "[commit|https://github.com/edx/edx-platform/commit/{sha}]"
    rows = [header]
    cbe = commits_by_email(from_commit, to_commit, include_merge)
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


def generate_email(from_commit, to_commit, release_date=None):
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
    """.format(
        emails=", ".join(sorted(emails(from_commit, to_commit))),
        date=release_date.isoformat(),
    )
    return textwrap.dedent(email).strip()


def main():
    parser = make_parser()
    args = parser.parse_args()
    if isinstance(args.date, basestring):
        # user passed in a custom date, so we need to parse it
        args.date = parse_datestring(args.date).date()

    if args.table:
        print(generate_table(args.previous, args.current, include_merge=args.merge))
        return

    print("EMAIL:")
    print(generate_email(args.previous, args.current, release_date=args.date))
    print("\n")
    print("Wiki Table:")
    print(
        "Type Ctrl+Shift+D on Confluence to embed the following table "
        "in your release wiki page"
    )
    print("\n")
    print(generate_table(args.previous, args.current, include_merge=args.merge))

if __name__ == "__main__":
    main()
