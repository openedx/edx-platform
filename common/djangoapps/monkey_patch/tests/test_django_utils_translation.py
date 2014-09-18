# -*- coding: utf-8 -*-
"""
Test methods exposed in common/lib/monkey_patch/django_utils_translation.py

Verify that the Django translation functions (gettext, ngettext,
pgettext, ugettext, and derivatives) all return the correct values
before, during, and after monkey-patching the django.utils.translation
module.

gettext, ngettext, pgettext, and ugettext must return a translation as
output for nonempty input.

ngettext, pgettext, npgettext, and ungettext must return an empty string
for an empty string as input.

gettext and ugettext will return translation headers, before and after
patching.

gettext and ugettext must return the empty string for any falsey input,
while patched.

*_noop must return the input text.

*_lazy must return the same text as their non-lazy counterparts.
"""
# pylint: disable=invalid-name
#  Let names like `gettext_*` stay lowercase; makes matching easier.
# pylint: disable=missing-docstring
#  All major functions are documented, the rest are self-evident shells.
# pylint: disable=no-member
#  Pylint doesn't see our decorator `translate_with` add the `_` method.
from unittest import TestCase

from ddt import data
from ddt import ddt
from django.utils.translation import _trans
from django.utils.translation import gettext
from django.utils.translation import gettext_lazy
from django.utils.translation import gettext_noop
from django.utils.translation import ngettext
from django.utils.translation import ngettext_lazy
from django.utils.translation import npgettext
from django.utils.translation import npgettext_lazy
from django.utils.translation import pgettext
from django.utils.translation import pgettext_lazy
from django.utils.translation import ugettext
from django.utils.translation import ugettext_lazy
from django.utils.translation import ugettext_noop
from django.utils.translation import ungettext
from django.utils.translation import ungettext_lazy

from monkey_patch.django_utils_translation import ATTRIBUTES as attributes_patched
from monkey_patch.django_utils_translation import is_patched
from monkey_patch.django_utils_translation import patch
from monkey_patch.django_utils_translation import unpatch

# Note: The commented-out function names are explicitly excluded, as
# they are not attributes of `django.utils.translation._trans`.
# https://github.com/django/django/blob/1.4.8/django/utils/translation/__init__.py#L69
attributes_not_patched = [
    'gettext_noop',
    'ngettext',
    'npgettext',
    'pgettext',
    'ungettext',
    # 'gettext_lazy',
    # 'ngettext_lazy',
    # 'npgettext_lazy',
    # 'pgettext_lazy',
    # 'ugettext_lazy',
    # 'ugettext_noop',
    # 'ungettext_lazy',
]


class MonkeyPatchTest(TestCase):
    def setUp(self):
        """
        Remember the current state, then reset
        """
        self.was_patched = unpatch()
        self.unpatch_all()
        self.addCleanup(self.cleanup)

    def cleanup(self):
        """
        Revert translation functions to previous state

        Since the end state varies, we always unpatch to remove any
        changes, then repatch again iff the module was already
        patched when the test began.
        """
        self.unpatch_all()
        if self.was_patched:
            patch()

    def unpatch_all(self):
        """
        Unpatch the module recursively
        """
        while is_patched():
            unpatch()


@ddt
class PatchTest(MonkeyPatchTest):
    """
    Verify monkey-patching and un-monkey-patching
    """
    @data(*attributes_not_patched)
    def test_not_patch(self, attribute_name):
        """
        Test that functions are not patched unintentionally
        """
        self.unpatch_all()
        old_attribute = getattr(_trans, attribute_name)
        patch()
        new_attribute = getattr(_trans, attribute_name)
        self.assertIs(old_attribute, new_attribute)

    @data(*attributes_patched)
    def test_unpatch(self, attribute):
        """
        Test that unpatch gracefully handles unpatched functions
        """
        patch()
        self.assertTrue(is_patched())
        self.unpatch_all()
        self.assertFalse(is_patched())
        old_attribute = getattr(_trans, attribute)
        self.unpatch_all()
        new_attribute = getattr(_trans, attribute)
        self.assertIs(old_attribute, new_attribute)
        self.assertFalse(is_patched())

    @data(*attributes_patched)
    def test_patch_attributes(self, attribute):
        """
        Test that patch changes the attribute
        """
        self.unpatch_all()
        self.assertFalse(is_patched())
        old_attribute = getattr(_trans, attribute)
        patch()
        new_attribute = getattr(_trans, attribute)
        self.assertIsNot(old_attribute, new_attribute)
        self.assertTrue(is_patched())
        old_attribute = getattr(_trans, attribute)
        patch()
        new_attribute = getattr(_trans, attribute)
        self.assertIsNot(old_attribute, new_attribute)
        self.assertTrue(is_patched())


def translate_with(function):
    """
    Decorate a class by setting its `_` translation function
    """
    def decorate(cls):
        def _(self, *args):
            # pylint: disable=unused-argument
            return function(*args)
        cls._ = _
        return cls
    return decorate


@translate_with(ugettext)
class UgettextTest(MonkeyPatchTest):
    """
    Test a Django translation function

    Here we consider `ugettext` to be the base/default case. All other
    translation functions extend, as needed.
    """
    is_unicode = True
    needs_patched = True
    header = 'Project-Id-Version: '

    def setUp(self):
        """
        Restore translation text and functions
        """
        super(UgettextTest, self).setUp()
        if self.is_unicode:
            self.empty = u''
            self.nonempty = u'(╯°□°）╯︵ ┻━┻'
        else:
            self.empty = ''
            self.nonempty = 'Hey! Where are you?!'

    def assert_translations(self):
        """
        Assert that the empty and nonempty translations are correct

        The `empty = empty[:]` syntax is intentional. Since subclasses
        may implement a lazy translation, we must perform a "string
        operation" to coerce it to a string value. We don't use `str` or
        `unicode` because we also assert the string type.
        """
        empty, nonempty = self.get_translations()
        empty = empty[:]
        nonempty = nonempty[:]
        if self.is_unicode:
            self.assertTrue(isinstance(empty, unicode))
            self.assertTrue(isinstance(nonempty, unicode))
        else:
            self.assertTrue(isinstance(empty, str))
            self.assertTrue(isinstance(nonempty, str))
        if self.needs_patched and not is_patched():
            self.assertIn(self.header, empty)
        else:
            self.assertNotIn(self.header, empty)
        self.assertNotIn(self.header, nonempty)

    def get_translations(self):
        """
        Translate the empty and nonempty strings, per `self._`
        """
        empty = self._(self.empty)
        nonempty = self._(self.nonempty)
        return (empty, nonempty)

    def test_patch(self):
        """
        Test that `self._` correctly translates text before, during, and
        after being monkey-patched.
        """
        self.assert_translations()
        was_successful = patch()
        self.assertTrue(was_successful)
        self.assert_translations()
        was_successful = unpatch()
        self.assertTrue(was_successful)
        self.assert_translations()


@translate_with(gettext)
class GettextTest(UgettextTest):
    is_unicode = False


@translate_with(pgettext)
class PgettextTest(UgettextTest):
    needs_patched = False
    l18n_context = 'monkey_patch'

    def get_translations(self):
        empty = self._(self.l18n_context, self.empty)
        nonempty = self._(self.l18n_context, self.nonempty)
        return (empty, nonempty)


@translate_with(ngettext)
class NgettextTest(GettextTest):
    number = 1
    needs_patched = False

    def get_translations(self):
        empty = self._(self.empty, self.empty, self.number)
        nonempty = self._(self.nonempty, self.nonempty, self.number)
        return (empty, nonempty)


@translate_with(npgettext)
class NpgettextTest(PgettextTest):
    number = 1

    def get_translations(self):
        empty = self._(self.l18n_context, self.empty, self.empty, self.number)
        nonempty = self._(self.l18n_context, self.nonempty, self.nonempty, self.number)
        return (empty, nonempty)


class NpgettextPluralTest(NpgettextTest):
    number = 2


class NgettextPluralTest(NgettextTest):
    number = 2


@translate_with(gettext_noop)
class GettextNoopTest(GettextTest):
    needs_patched = False


@translate_with(ugettext_noop)
class UgettextNoopTest(UgettextTest):
    needs_patched = False


@translate_with(ungettext)
class UngettextTest(NgettextTest):
    is_unicode = True


class UngettextPluralTest(UngettextTest):
    number = 2


@translate_with(gettext_lazy)
class GettextLazyTest(GettextTest):
    pass


@translate_with(ugettext_lazy)
class UgettextLazyTest(UgettextTest):
    pass


@translate_with(pgettext_lazy)
class PgettextLazyTest(PgettextTest):
    pass


@translate_with(ngettext_lazy)
class NgettextLazyTest(NgettextTest):
    pass


@translate_with(npgettext_lazy)
class NpgettextLazyTest(NpgettextTest):
    pass


class NpgettextLazyPluralTest(NpgettextLazyTest):
    number = 2


@translate_with(ungettext_lazy)
class UngettextLazyTest(UngettextTest):
    pass
