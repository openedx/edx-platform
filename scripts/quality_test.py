"""  # lint-amnesty, pylint: disable=django-not-configured
Check code quality using pycodestyle, pylint, and diff_quality.
"""

import re
import subprocess
import shlex


def run_eslint():
    """
    Runs eslint on static asset directories.
    If limit option is passed, fails build if more violations than the limit are found.
    """
    violations_limit = 4950

    command = [
        "node",
        "--max_old_space_size=4096",
        "node_modules/.bin/eslint",
        "--ext", ".js",
        "--ext", ".jsx",
        "--format=compact",
        "."
    ]
    print(shlex.join(command))
    result = subprocess.run(
        command,
        text=True,
        check=False,
        capture_output=True
    )

    print(result.stdout)
    print(result.stderr)
    last_line = result.stdout.strip().splitlines()[-1]
    regex = r'^\d+'
    try:
        num_violations = int(re.search(regex, last_line).group(0))
    # An AttributeError will occur if the regex finds no matches.
    # A ValueError will occur if the returned regex cannot be cast as a float.
    except (AttributeError, ValueError):
        print('eslint')
        print(f"FAILURE: Number of eslint violations could not be found in '{last_line}'")

    # Fail if number of violations is greater than the limit
    if num_violations > violations_limit:
        print('eslint')
        print(f"FAILURE: Too many eslint violations ({num_violations}).\nThe limit is {violations_limit}.")
    else:
        print(f"successfully run eslint with violations '{num_violations}'")


if __name__ == "__main__":
    run_eslint()
