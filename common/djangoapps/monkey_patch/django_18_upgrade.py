"""
Super-temporary hack to get past some import errors to find more problems.
TNL-3387
"""


def scare(msg):
    """Print a message in a really noticeable way."""
    print "**\n**\n** {}\n**\n**\n".format(msg)

import django.db.transaction

scare("Monkey-patching django.db.transaction: see TNL-3387")


def do_nothing(f):
    """A do-nothing decorator to let us defer deciding what to do with commit_manually being gone."""
    scare("Using fake django.db.transaction decorator on {name} in {file} at {line}".format(
        name=f.func_name,
        file=f.func_code.co_filename,
        line=f.func_code.co_firstlineno,
    ))
    return f

django.db.transaction.commit_manually = do_nothing
django.db.transaction.commit_on_success = do_nothing
django.db.transaction.autocommit = do_nothing
