"""
Super-temporary hack to get past some import errors to find more problems.
TNL-3387
"""

def scare(msg):
    """Print a message in a really noticeable way."""
    print "**\n**\n** {}!!!\n**\n**\n".format(msg)

import django.db.transaction

scare("Monkey-patching django.db.transaction: see TNL-3387")

def commit_manually(f):
    """A do-nothing decorator to let us defer deciding what to do with commit_manually being gone."""
    scare("Using fake commit_manually on {}".format(f))
    return f

django.db.transaction.commit_manually = commit_manually
