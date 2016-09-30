#!/usr/bin/env python
"""
a release-master multitool
"""
from __future__ import print_function, unicode_literals
import sys
import argparse
from datetime import date, timedelta
import re
import collections
import functools
import textwrap
import json
import getpass

try:
    from path import Path as path
    from git import Repo, Commit
    from git.refs.symbolic import SymbolicReference
    from dateutil.parser import parse as parse_datestring
    import requests
    import yaml
except ImportError:
    print("Error: missing dependencies! Please run this command to install them:")
    print("pip install path.py requests python-dateutil GitPython PyYAML")
    sys.exit(1)

try:
    from pygments.console import colorize
except ImportError:
    colorize = lambda color, text: text

JIRA_RE = re.compile(r"\b[A-Z]{2,}-\d+\b")
PR_BRANCH_RE = re.compile(r"remotes/edx/pr/(\d+)")


def project_root():
    directory = path(__file__).abspath().dirname()
    while not (directory / ".git").exists():
        directory = directory.parent
    return directory


PROJECT_ROOT = project_root()
repo = Repo(PROJECT_ROOT)
git = repo.git

PEOPLE_YAML = "https://raw.githubusercontent.com/edx/repo-tools-data/master/people.yaml"


class memoized(object):
    """
    Decorator. Caches a function's return value each time it is called.
    If called later with the same arguments, the cached value is returned
    (not reevaluated).

    https://wiki.python.org/moin/PythonDecoratorLibrary#Memoize
    """
    def __init__(self, func):
        self.func = func
        self.cache = {}

    def __call__(self, *args):
        if not isinstance(args, collections.Hashable):
            # uncacheable. a list, for instance.
            # better to not cache than blow up.
            return self.func(*args)
        if args in self.cache:
            return self.cache[args]
        else:
            value = self.func(*args)
            self.cache[args] = value
            return value

    def __repr__(self):
        '''Return the function's docstring.'''
        return self.func.__doc__

    def __get__(self, obj, objtype):
        '''Support instance methods.'''
        return functools.partial(self.__call__, obj)


def make_parser():
    parser = argparse.ArgumentParser(description="release master multitool")
    parser.add_argument(
        '--previous', '--prev', '-p', metavar="GITREV", default="edx/release",
        help="previous release [%(default)s]")
    parser.add_argument(
        '--current', '--curr', '-c', metavar="GITREV", default="HEAD",
        help="current release candidate [%(default)s]")
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


def ensure_pr_fetch():
    """
    Make sure that the git repository contains a remote called "edx" that has
    two fetch URLs; one for the main codebase, and one for pull requests.
    Returns True if the environment was modified in any way, False otherwise.
    """
    modified = False
    remotes = git.remote().splitlines()
    if 'edx' not in remotes:
        git.remote("add", "edx", "https://github.com/edx/edx-platform.git")
        modified = True
    # it would be nice to use the git-python API to do this, but it doesn't seem
    # to support configurations with more than one value per key. :(
    edx_fetches = git.config("remote.edx.fetch", get_all=True).splitlines()
    pr_fetch = '+refs/pull/*/head:refs/remotes/edx/pr/*'
    if pr_fetch not in edx_fetches:
        git.config("remote.edx.fetch", pr_fetch, add=True)
        modified = True
    git.fetch("edx")
    return modified


def get_github_creds():
    """
    Returns GitHub credentials if they exist, as a two-tuple of (username, token).
    Otherwise, return None.
    """
    netrc_auth = requests.utils.get_netrc_auth("https://api.github.com")
    if netrc_auth:
        return netrc_auth
    config_file = path("~/.config/edx-release").expand()
    if config_file.isfile():
        with open(config_file) as f:
            config = json.load(f)
        github_creds = config.get("credentials", {}).get("api.github.com", {})
        username = github_creds.get("username", "")
        token = github_creds.get("token", "")
        if username and token:
            return (username, token)
    return None


def create_github_creds():
    """
    https://developer.github.com/v3/oauth_authorizations/#create-a-new-authorization
    """
    headers = {"User-Agent": "edx-release"}
    payload = {
        "note": "edx-release",
        "scopes": ["repo"],
    }
    username = raw_input("GitHub username: ")
    password = getpass.getpass("GitHub password: ")
    response = requests.post(
        "https://api.github.com/authorizations",
        auth=(username, password),
        headers=headers, data=json.dumps(payload),
    )
    # is the user using two-factor authentication?
    otp_header = response.headers.get("X-GitHub-OTP")
    if not response.ok and otp_header and otp_header.startswith("required;"):
        # get two-factor code, redo the request
        headers["X-GitHub-OTP"] = raw_input("Two-factor authentication code: ")
        response = requests.post(
            "https://api.github.com/authorizations",
            auth=(username, password),
            headers=headers, data=json.dumps(payload),
        )
    if not response.ok:
        message = response.json()["message"]
        if message != "Validation Failed":
            raise requests.exceptions.RequestException(message)
        else:
            # A token called "edx-release" already exists on GitHub.
            # Delete it, and try again.
            token_id = get_github_auth_id(username, password, "edx-release")
            if token_id:
                delete_github_auth_token(username, password, token_id)
            response = requests.post(
                "https://api.github.com/authorizations",
                auth=(username, password),
                headers=headers, data=json.dumps(payload),
            )
    if not response.ok:
        message = response.json()["message"]
        raise requests.exceptions.RequestException(message)

    return (username, response.json()["token"])


def get_github_auth_id(username, password, note):
    """
    Return the ID associated with the GitHub auth token with the given note.
    If no such auth token exists, return None.
    """
    response = requests.get(
        "https://api.github.com/authorizations",
        auth=(username, password),
        headers={"User-Agent": "edx-release"},
    )
    if not response.ok:
        message = response.json()["message"]
        raise requests.exceptions.RequestException(message)

    for auth_token in response.json():
        if auth_token["note"] == "edx-release":
            return auth_token["id"]
    return None


def delete_github_auth_token(username, password, token_id):
    response = requests.delete(
        "https://api.github.com/authorizations/{id}".format(id=token_id),
        auth=(username, password),
        headers={"User-Agent": "edx-release"},
    )
    if not response.ok:
        message = response.json()["message"]
        raise requests.exceptions.RequestException(message)


def ensure_github_creds(attempts=3):
    """
    Make sure that we have GitHub OAuth credentials. This will check the user's
    .netrc file, as well as the ~/.config/edx-release file. If no credentials
    exist in either place, it will prompt the user to create OAuth credentials,
    and store them in ~/.config/edx-release.

    Returns False if we found credentials, True if we had to create them.
    """
    if get_github_creds():
        return False

    # Looks like we need to create the OAuth creds
    print("We need to set up OAuth authentication with GitHub's API. "
          "Your password will not be stored.", file=sys.stderr)
    token = None
    for _ in range(attempts):
        try:
            username, token = create_github_creds()
        except requests.exceptions.RequestException as e:
            print(
                "Invalid authentication: {}".format(e.message),
                file=sys.stderr,
            )
            continue
        else:
            break
    if token:
        print("Successfully authenticated to GitHub", file=sys.stderr)
    if not token:
        print("Too many invalid authentication attempts.", file=sys.stderr)
        return False

    config_file = path("~/.config/edx-release").expand()
    # make sure parent directory exists
    config_file.parent.makedirs_p()
    # read existing config if it exists
    if config_file.isfile():
        with open(config_file) as f:
            config = json.load(f)
    else:
        config = {}
    # update config
    if 'credentials' not in config:
        config["credentials"] = {}
    if 'api.github.com' not in config['credentials']:
        config["credentials"]["api.github.com"] = {}
    config["credentials"]["api.github.com"]["username"] = username
    config["credentials"]["api.github.com"]["token"] = token
    # write it back out
    with open(config_file, "w") as f:
        json.dump(config, f)

    return True


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
    return set(JIRA_RE.findall(text))


class DoesNotExist(Exception):
    def __init__(self, message, commit, branch):
        self.message = message
        self.commit = commit
        self.branch = branch
        Exception.__init__(self, message)


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
    # no merge commit!
    msg = "No merge commit for {commit} in {branch}!".format(
        commit=commit, branch=branch,
    )
    raise DoesNotExist(msg, commit, branch)


def get_pr_info(num):
    """
    Returns the info from the GitHub API
    """
    url = "https://api.github.com/repos/edx/edx-platform/pulls/{num}".format(num=num)
    username, token = get_github_creds()
    headers = {
        "Authorization": "token {}".format(token),
        "User-Agent": "edx-release",
    }
    response = requests.get(url, headers=headers)
    result = response.json()
    if not response.ok:
        raise requests.exceptions.RequestException(result["message"])
    return result


def get_merged_prs(start_ref, end_ref):
    """
    Return the set of all pull requests (as integers) that were merged between
    the start_ref and end_ref.
    """
    ensure_pr_fetch()
    start_unmerged_branches = set(
        branch.strip() for branch in
        git.branch(all=True, no_merged=start_ref).splitlines()
    )
    end_merged_branches = set(
        branch.strip() for branch in
        git.branch(all=True, merged=end_ref).splitlines()
    )
    merged_between_refs = start_unmerged_branches & end_merged_branches
    merged_prs = set()
    for branch in merged_between_refs:
        match = PR_BRANCH_RE.search(branch)
        if match:
            merged_prs.add(int(match.group(1)))
    return merged_prs


@memoized
def prs_by_email(start_ref, end_ref):
    """
    Returns an ordered dictionary of {email: pr_list}
    Email is the email address of the person who merged the pull request
    The dictionary is alphabetically ordered by email address
    The pull request list is ordered by merge date
    """
    username, token = get_github_creds()
    headers = {
        "Authorization": "token {}".format(token),
        "User-Agent": "edx-release",
    }
    # `emails` maps from other_emails to primary email, based on people.yaml.
    emails = {}
    people_resp = requests.get(PEOPLE_YAML, headers=headers)
    people_resp.raise_for_status()
    people = yaml.safe_load(people_resp.text)
    for person in people.itervalues():
        if 'other_emails' in person:
            for other_email in person['other_emails']:
                emails[other_email] = person['email']

    unordered_data = collections.defaultdict(set)
    for pr_num in get_merged_prs(start_ref, end_ref):
        ref = "refs/remotes/edx/pr/{num}".format(num=pr_num)
        branch = SymbolicReference(repo, ref)
        try:
            merge = get_merge_commit(branch.commit, end_ref)
        except DoesNotExist:
            pass  # this commit will be included in the commits_without_prs table
        else:
            email = emails.get(merge.author.email, merge.author.email)
            if email.endswith("@users.noreply.github.com"):
                # A bogus GitHub address, look up their GitHub name in
                # people.yaml
                username = email.split("@")[0]
                try:
                    email = people[username]['email']
                except KeyError:
                    pass
            unordered_data[email].add((pr_num, merge))

    ordered_data = collections.OrderedDict()
    for email in sorted(unordered_data.keys()):
        ordered = sorted(unordered_data[email], key=lambda pair: pair[1].authored_date)
        ordered_data[email] = [num for num, merge in ordered]
    return ordered_data


def generate_pr_table(start_ref, end_ref):
    """
    Return a UTF-8 string corresponding to a pull request table to embed in Confluence.
    """
    header = "|| Merged By || Author || Title || PR || JIRA || Release Notes? || Verified? ||"
    pr_link = "[#{num}|https://github.com/edx/edx-platform/pull/{num}]"
    user_link = "[@{user}|https://github.com/{user}]"
    rows = [header]
    prbe = prs_by_email(start_ref, end_ref)
    for email, pull_requests in prbe.items():
        for i, pull_request in enumerate(pull_requests):
            try:
                pr_info = get_pr_info(pull_request)
                title = pr_info["title"] or ""
                body = pr_info["body"] or ""
                author = pr_info["user"]["login"]
            except requests.exceptions.RequestException as e:
                message = (
                    "Warning: could not fetch data for #{num}: "
                    "{message}".format(num=pull_request, message=e.message)
                )
                print(colorize("red", message), file=sys.stderr)
                title = "?"
                body = "?"
                author = ""
            rows.append("| {merged_by} | {author} | {title} | {pull_request} | {jira} | {release_notes} | {verified} |".format(
                merged_by=email if i == 0 else "",
                author=user_link.format(user=author) if author else "",
                title=title.replace("|", "\|").replace('{', '\{').replace('}', '\}'),
                pull_request=pr_link.format(num=pull_request),
                jira=", ".join(parse_ticket_references(body)),
                release_notes="",
                verified="",
            ))
    return "\n".join(rows).encode("utf8")


@memoized
def get_commits_not_in_prs(start_ref, end_ref):
    """
    Return a tuple of commits that exist between start_ref and end_ref,
    but were not merged to the end_ref. If everyone is following the
    pull request process correctly, this should return an empty tuple.
    """
    return tuple(Commit.iter_items(
        repo,
        "{start}..{end}".format(start=start_ref, end=end_ref),
        first_parent=True, no_merges=True,
    ))


def generate_commit_table(start_ref, end_ref):
    """
    Return a string corresponding to a commit table to embed in Comfluence.
    The commits in the table should only be commits that are not in the
    pull request table.
    """
    header = "|| Author || Summary || Commit || JIRA || Release Notes? || Verified? ||"
    commit_link = "[commit|https://github.com/edx/edx-platform/commit/{sha}]"
    rows = [header]
    commits = get_commits_not_in_prs(start_ref, end_ref)
    for commit in commits:
        rows.append("| {author} | {summary} | {commit} | {jira} | {release_notes} | {verified} |".format(
            author=commit.author.email,
            summary=commit.summary.replace("|", "\|"),
            commit=commit_link.format(sha=commit.hexsha),
            jira=", ".join(parse_ticket_references(commit.message)),
            release_notes="",
            verified="",
        ))
    return "\n".join(rows)


def generate_email_recipients(start_ref, end_ref, release_date=None):
    """
    Returns a comma-separate string of email addresses associated with
    merged pull requests.
    """
    if release_date is None:
        release_date = default_release_date()
    prbe = prs_by_email(start_ref, end_ref)
    emails = ", ".join(prbe.keys())
    return emails


def main():
    parser = make_parser()
    args = parser.parse_args()
    if isinstance(args.date, basestring):
        # user passed in a custom date, so we need to parse it
        args.date = parse_datestring(args.date).date()

    ensure_github_creds()

    if args.table:
        print(generate_pr_table(args.previous, args.current))
        return

    print("Generating list of email recipients. This may take around a minute...")
    print(generate_email_recipients(args.previous, args.current, release_date=args.date).encode('UTF-8'))
    print("\n")
    print("Wiki Table:")
    print(
        "Type Ctrl+Shift+D on Confluence to embed the following table "
        "in your release wiki page"
    )
    print("\n")
    print(generate_pr_table(args.previous, args.current))
    commits_without_prs = get_commits_not_in_prs(args.previous, args.current)
    if commits_without_prs:
        num = len(commits_without_prs)
        plural = num > 1
        print("\n")
        print(
            "There {are} {num} {commits} in this release that did not come in "
            "through pull requests!".format(
                num=num, are="are" if plural else "is",
                commits="commits" if plural else "commit"
            )
        )
        print("\n")
        print(generate_commit_table(args.previous, args.current))


if __name__ == "__main__":
    main()
