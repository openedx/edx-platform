""" Errors used by the Discussion API. """


from django.core.exceptions import ObjectDoesNotExist


class DiscussionDisabledError(ObjectDoesNotExist):
    """ Discussion is disabled. """
    pass  # lint-amnesty, pylint: disable=unnecessary-pass


class ThreadNotFoundError(ObjectDoesNotExist):
    """ Thread was not found. """
    pass  # lint-amnesty, pylint: disable=unnecessary-pass


class CommentNotFoundError(ObjectDoesNotExist):
    """ Comment was not found. """
    pass  # lint-amnesty, pylint: disable=unnecessary-pass
