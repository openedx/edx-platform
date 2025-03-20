"""  # pylint: disable=django-not-configured
Check code quality using eslint.
"""

import re
import subprocess
import shlex
import sys


class BuildFailure(Exception):
    pass


def fail_quality(message):
    """
    Fail the specified quality check.
    """

    raise BuildFailure(message)


def run_eslint():
    """
    Runs eslint on static asset directories.
    If limit option is passed, fails build if more violations than the limit are found.
    """
    violations_limit = 625

    command = [
        "node",
        "--max_old_space_size=4096",
        "node_modules/.bin/eslint",
        "--ext", ".js",
        "--ext", ".jsx",
        "--format=compact",
        "lms",
        "cms",
        "common",
        "openedx",
        "xmodule",
    ]
    print("Running command:", shlex.join(command))
    result = subprocess.run(
        command,
        text=True,
        check=False,
        capture_output=True
    )

    print(result.stdout)
    if result.returncode == 0:
        fail_quality("No eslint violations found. This is unexpected... are you sure eslint is running correctly?")
    elif result.returncode == 1:
        last_line = result.stdout.strip().splitlines()[-1] if result.stdout.strip().splitlines() else ""
        regex = r'^\d+'
        try:
            num_violations = int(re.search(regex, last_line).group(0)) if last_line else 0
            # Fail if number of violations is greater than the limit
            if num_violations > violations_limit:
                fail_quality("FAILURE: Too many eslint violations ({count}).\nThe limit is {violations_limit}.".format(count=num_violations, violations_limit=violations_limit))
            else:
                print(f"successfully run eslint with '{num_violations}' violations")

        # An AttributeError will occur if the regex finds no matches.
        except (AttributeError, ValueError):
            fail_quality(f"FAILURE: Number of eslint violations could not be found in '{last_line}'")
    else:
        print(f"Unexpected ESLint failure with exit code {result.returncode}.")
        fail_quality(f"Unexpected error: {result.stderr.strip()}")


if __name__ == "__main__":
    try:
        run_eslint()
    except BuildFailure as e:
        print(e)
        sys.exit(1)
