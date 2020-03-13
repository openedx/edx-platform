"""
@@TODO
"""
from collections import defaultdict

from paver.easy import call_task, cmdopts, consume_args, needs, no_help, path, sh, task

@task

@no_help
@cmdopts([
    ('dir=', 'd', 'The directory to check.'),
])
def dircheck(options):
    """
    @@TODO
    """
    pylint_output_lines = get_pylint_output()
    pylint_issues_by_type = defaultdict(lambda: [])
    for line in pylint_output_lines:
        message_type, a, b, c, d = parse(line)
        pylint_issues_by_type[message_type.lower()].append(aggregate(a, b, c, d))
    # @@TODO

