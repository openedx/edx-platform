"""
New key/locator types that work with Blockstore and the new "Learning Context"
concept.

We will probably move these key types into the "opaque-keys" repository once
they are stable.
"""
# Disable warnings about _to_deprecated_string etc. which we don't want to implement.
# And fix warnings about key fields, which pylint doesn't see as member variables.
# pylint: disable=abstract-method, no-member
from __future__ import absolute_import, division, print_function, unicode_literals
import re
from uuid import UUID
import warnings

from opaque_keys import InvalidKeyError, OpaqueKey
from opaque_keys.edx.keys import DefinitionKey, UsageKey
import six


def check_key_string_field(value, regexp=r'^[\w\-.]+$'):
    """
    Helper method to verify that a key's string field(s) meet certain
    requirements:
        Are a non-empty string
        Match the specified regular expression
    """
    if not isinstance(value, six.string_types):
        raise TypeError("Expected a string")
    if not value or not re.match(regexp, value):
        raise ValueError("'{}' is not a valid field value for this key type.".format(value))


def check_draft_name(value):
    """
    Check that the draft name is valid (unambiguously not a bundle version
    nubmer).

    Valid: studio_draft, foo-bar, import348975938
    Invalid: 1, 15, 873452847357834
    """
    if not isinstance(value, six.string_types) or not value:
        raise TypeError("Expected a non-empty string")
    if value.isdigit():
        raise ValueError("Cannot use an integer draft name as it conflicts with bundle version nubmers")


class BundleDefinitionLocator(DefinitionKey):
    """
    Implementation of the DefinitionKey type, for XBlock content stored in
    Blockstore bundles. This is a low-level identifier used within the Open edX
    system for identifying and retrieving OLX.

    A "Definition" is a specific OLX file in a specific BundleVersion
    (or sometimes rather than a BundleVersion, it may point to a named draft.)
    The OLX file, and thus the definition key, defines Scope.content fields as
    well as defaults for Scope.settings and Scope.children fields. However the
    definition has no parent and no position in any particular course or other
    context - both of which require a *usage key* and not just a definition key.
    The same block definition (.olx file) can be used in multiple places in a
    course, each with a different usage key.

    Example serialized definition keys follow.

    The 'html' type OLX file "html/introduction/definition.xml" in bundle
    11111111-1111-1111-1111-111111111111, bundle version 5:

        bundle-olx:11111111-1111-1111-1111-111111111111:5:html:html/introduction/definition.xml

    The 'problem' type OLX file "problem324234.xml" in bundle
    22222222-2222-2222-2222-222222222222, draft 'studio-draft':

        bundle-olx:22222222-2222-2222-2222-222222222222:studio-draft:problem:problem/324234.xml

    (The serialized version is somewhat long and verbose because it should
    rarely be used except for debugging - the in-memory python key instance will
    be used most of the time, and users will rarely/never see definition keys.)

    User state should never be stored using a BundleDefinitionLocator as the
    key. State should always be stored against a usage locator, which refers to
    a particular definition being used in a particular context.

    Each BundleDefinitionLocator holds the following data
        1. Bundle UUID and [bundle version OR draft name]
        2. Block type (e.g. 'html', 'problem', etc.)
        3. Path to OLX file

    Note that since the data in an .olx file can only ever change in a bundle
    draft (not in a specific bundle version), an XBlock that is actively making
    changes to its Scope.content/Scope.settings field values must have a
    BundleDefinitionLocator with a draft name (not a bundle version).
    """
    CANONICAL_NAMESPACE = 'bundle-olx'
    KEY_FIELDS = ('bundle_uuid', 'block_type', 'olx_path', '_version_or_draft')
    __slots__ = KEY_FIELDS
    CHECKED_INIT = False

    def __init__(self, bundle_uuid, block_type, olx_path, bundle_version=None, draft_name=None, _version_or_draft=None):
        """
        Instantiate a new BundleDefinitionLocator
        """
        if not isinstance(bundle_uuid, UUID):
            bundle_uuid = UUID(bundle_uuid)
        check_key_string_field(block_type)
        check_key_string_field(olx_path, regexp=r'^[\w\-./]+$')
        # For now the following is a convention; we could remove this restriction in the future given new use cases.
        assert block_type + '/' in olx_path, 'path should contain block type, e.g. html/id/definition.xml for html'

        if (bundle_version is not None) + (draft_name is not None) + (_version_or_draft is not None) != 1:
            raise ValueError("Exactly one of [bundle_version, draft_name, _version_or_draft] must be specified")
        if _version_or_draft is not None:
            if isinstance(_version_or_draft, int):
                pass  # This is a bundle version number.
            else:
                # This is a draft name, not a bundle version:
                check_draft_name(_version_or_draft)
        elif draft_name is not None:
            check_draft_name(draft_name)
            _version_or_draft = draft_name
        else:
            assert isinstance(bundle_version, int)
            _version_or_draft = bundle_version

        super(BundleDefinitionLocator, self).__init__(
            bundle_uuid=bundle_uuid,
            block_type=block_type,
            olx_path=olx_path,
            _version_or_draft=_version_or_draft,
        )

    @property
    def bundle_version(self):
        return self._version_or_draft if isinstance(self._version_or_draft, int) else None

    @property
    def draft_name(self):
        return self._version_or_draft if not isinstance(self._version_or_draft, int) else None

    def _to_string(self):
        """
        Return a string representing this BundleDefinitionLocator
        """
        return ":".join((
            six.text_type(self.bundle_uuid), six.text_type(self._version_or_draft), self.block_type, self.olx_path,
        ))

    @classmethod
    def _from_string(cls, serialized):
        """
        Return a BundleDefinitionLocator by parsing the given serialized string
        """
        try:
            (bundle_uuid_str, _version_or_draft, block_type, olx_path) = serialized.split(':', 3)
        except ValueError:
            raise InvalidKeyError(cls, serialized)

        bundle_uuid = UUID(bundle_uuid_str)
        if not block_type or not olx_path:
            raise InvalidKeyError(cls, serialized)

        if _version_or_draft.isdigit():
            _version_or_draft = int(_version_or_draft)

        return cls(
            bundle_uuid=bundle_uuid,
            block_type=block_type,
            olx_path=olx_path,
            _version_or_draft=_version_or_draft,
        )


class LearningContextKey(OpaqueKey):
    """
    A key that idenitifies a course, a library, a program,
    or some other collection of content where learning happens.
    """
    KEY_TYPE = 'context_key'
    __slots__ = ()

    def make_definition_usage(self, definition_key, usage_id=None):
        """
        Return a usage key, given the given the specified definition key and
        usage_id.
        """
        raise NotImplementedError()


class BlockUsageKeyV2(UsageKey):
    """
    Abstract base class that encodes an XBlock used in a specific learning
    context (e.g. a course).

    Definition + Learning Context = Usage
    """
    @property
    def context_key(self):
        raise NotImplementedError()

    @property
    def definition_key(self):
        """
        Returns the definition key for this usage.
        """
        # Because this key definition is likely going to be moved into the
        # opaque-keys package, we cannot put the logic here for getting the
        # definition.
        raise NotImplementedError(
            "To get the definition key, use: "
            "get_learning_context_impl(usage_key).definition_for_usage(usage_key)"
        )

    @property
    def course_key(self):
        warnings.warn("Use .context_key instead of .course_key", DeprecationWarning, stacklevel=2)
        return self.context_key

    def html_id(self):
        """
        Return an id which can be used on an html page as an id attr of an html
        element. This is only in here for backwards-compatibility with XModules;
        don't use in new code.
        """
        warnings.warn(".html_id is deprecated", DeprecationWarning, stacklevel=2)
        # HTML5 allows ID values to contain any characters at all other than spaces.
        # These key types don't allow spaces either, so no transform is needed.
        return six.text_type(self)
