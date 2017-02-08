#!/usr/bin/env python
"""
Script to generate alton and git commands for executing hotfixes
Commands for:
  - cutting amis
  - creating hotfix tag

The script should be run with the hotfix's git hash as a command-line argument.
i.e. `python scripts/hotfix.py <hotfix hash>`
"""
from __future__ import print_function
from datetime import date
import sys
import argparse
import textwrap


def generate_alton_commands(hotfix_hash):
    """
    Generates commands for alton to cut amis from the git hash of the hotfix.
    """
    template = textwrap.dedent("""
    @alton cut ami for stage-edx-edxapp from prod-edx-edxapp with edx_platform_version={hotfix_hash}
    @alton cut ami for prod-edge-edxapp from prod-edge-edxapp with edx_platform_version={hotfix_hash}
    @alton cut ami for prod-edx-edxapp from prod-edx-edxapp with edx_platform_version={hotfix_hash}
    """)
    return template.strip().format(hotfix_hash=hotfix_hash)


def generate_git_command(hotfix_hash):
    """
    Generates command to tag the git hash of the hotfix.
    """
    git_string = 'git tag -a hotfix-{iso_date} -m "Hotfix for {msg_date}" {hotfix_hash}'.format(
        iso_date=date.today().isoformat(),
        msg_date=date.today().strftime("%b %d, %Y"),
        hotfix_hash=hotfix_hash,
    )
    return git_string


def main():
    parser = argparse.ArgumentParser(description="Generate alton and git commands for hotfixes")
    parser.add_argument("hash", help="git hash for hotfix")
    args = parser.parse_args()

    hotfix_hash = args.hash

    print("\nHere are the alton commands to cut the hotfix amis:")
    print(generate_alton_commands(hotfix_hash))

    print("\nHere is the git command to generate the hotfix tag:")
    print(generate_git_command(hotfix_hash))

    print("\nOnce you create the git tag, push the tag by running:")
    print("git push --tags\n")


if __name__ == '__main__':
    main()
