"""
Monkey-patch `django.utils.translation` to not dump header info

Modify Django's translation module, such that the *gettext functions
always return an empty string when attempting to translate an empty
string. This overrides the default behavior [0]:
> It is convention with GNU gettext to include meta-data as the
> translation for the empty string.

Affected Methods:
    - gettext
    - ugettext

Note: The *ngettext and *pgettext functions are intentionally omitted,
as they already behave as expected. The *_lazy functions are implicitly
patched, as they wrap their nonlazy equivalents.

Django's translation module contains a good deal of indirection. For us
to patch the module with our own functions, we have to patch
`django.utils.translation._trans`. This ensures that the patched
behavior will still be used, even if code elsewhere caches a reference
to one of the translation functions. If you're curious, check out
Django's source code [1].

[0] https://docs.python.org/2.7/library/gettext.html#the-gnutranslations-class
[1] https://github.com/django/django/blob/1.4.8/django/utils/translation/__init__.py#L66
"""
from django.utils.translation import _trans as translation

import monkey_patch

ATTRIBUTES = [
    'gettext',
    'ugettext',
]


def is_patched():
    """
    Check if the translation module has been monkey-patched
    """
    patched = True
    for attribute in ATTRIBUTES:
        if not monkey_patch.is_patched(translation, attribute):
            patched = False
            break
    return patched


def patch():
    """
    Monkey-patch the translation functions

    Affected Methods:
        - gettext
        - ugettext
    """
    def decorate(function, message_default=u''):
        """
        Decorate a translation function

        Default message is a unicode string, but gettext overrides this
        value to return a UTF8 string.
        """
        def dont_translate_empty_string(message):
            """
            Return the empty string when passed a falsey message
            """
            if message:
                message = function(message)
            else:
                message = message_default
            return message
        return dont_translate_empty_string
    gettext = decorate(translation.gettext, '')
    ugettext = decorate(translation.ugettext)
    monkey_patch.patch(translation, 'gettext', gettext)
    monkey_patch.patch(translation, 'ugettext', ugettext)
    return is_patched()


def unpatch():
    """
    Un-monkey-patch the translation functions
    """
    was_patched = False
    for name in ATTRIBUTES:
        # was_patched must be the second half of the or-clause, to avoid
        # short-circuiting the expression
        was_patched = monkey_patch.unpatch(translation, name) or was_patched
    return was_patched
