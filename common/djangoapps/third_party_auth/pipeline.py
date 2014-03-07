"""Auth pipeline definitions."""

from social.pipeline import partial


@partial.partial
def step(*args, **kwargs):
    """Fake pipeline step; just throws loudly for now."""
    raise NotImplementedError('%s, %s' % (args, kwargs))
