# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

from __future__ import print_function
import json
import os
import pprint
import sys
import warnings

try:
    from jsonschema import ValidationError
    from jsonschema import Draft4Validator as Validator
except ImportError as e:
    verbose_msg = """

    Jupyter notebook format depends on the jsonschema package:

        https://pypi.python.org/pypi/jsonschema

    Please install it first.
    """
    raise ImportError(str(e) + verbose_msg)

from ipython_genutils.importstring import import_item


validators = {}

def _relax_additional_properties(obj):
    """relax any `additionalProperties`"""
    if isinstance(obj, dict):
        for key, value in obj.items():
            if key == 'additionalProperties':
                value = True
            else:
                value = _relax_additional_properties(value)
            obj[key] = value
    elif isinstance(obj, list):
        for i, value in enumerate(obj):
            obj[i] = _relax_additional_properties(value)
    return obj

def _allow_undefined(schema):
    schema['definitions']['cell']['oneOf'].append(
        {"$ref": "#/definitions/unrecognized_cell"}
    )
    schema['definitions']['output']['oneOf'].append(
        {"$ref": "#/definitions/unrecognized_output"}
    )
    return schema

def get_validator(version=None, version_minor=None, relax_add_props=False):
    """Load the JSON schema into a Validator"""
    if version is None:
        from .. import current_nbformat
        version = current_nbformat

    v = import_item("nbformat.v%s" % version)
    current_minor = getattr(v, 'nbformat_minor', 0)
    if version_minor is None:
        version_minor = current_minor

    version_tuple = (version, version_minor)

    if version_tuple not in validators:
        try:
            schema_json = _get_schema_json(v)
        except AttributeError:
            return None

        if current_minor < version_minor:
            # notebook from the future, relax all `additionalProperties: False` requirements
            schema_json = _relax_additional_properties(schema_json)
            # and allow undefined cell types and outputs
            schema_json = _allow_undefined(schema_json)

        validators[version_tuple] = Validator(schema_json)

    if relax_add_props:
        try:
            schema_json = _get_schema_json(v)
        except AttributeError:
            return None

        # this allows properties to be added for intermediate
        # representations while validating for all other kinds of errors
        schema_json = _relax_additional_properties(schema_json)

        validators[version_tuple] = Validator(schema_json)
    return validators[version_tuple]


def _get_schema_json(v):
    """
    Gets the json schema from a given imported library a nbformat version.
    """
    schema_path = os.path.join(os.path.dirname(v.__file__), v.nbformat_schema)
    with open(schema_path) as f:
        schema_json = json.load(f)
    return schema_json

def isvalid(nbjson, ref=None, version=None, version_minor=None):
    """Checks whether the given notebook JSON conforms to the current
    notebook format schema. Returns True if the JSON is valid, and
    False otherwise.

    To see the individual errors that were encountered, please use the
    `validate` function instead.
    """
    try:
        validate(nbjson, ref, version, version_minor)
    except ValidationError:
        return False
    else:
        return True

def _format_as_index(indices):
    """
    (from jsonschema._utils.format_as_index, copied to avoid relying on private API)

    Construct a single string containing indexing operations for the indices.

    For example, [1, 2, "foo"] -> [1][2]["foo"]
    """

    if not indices:
        return ""
    return "[%s]" % "][".join(repr(index) for index in indices)

_ITEM_LIMIT = 16
_STR_LIMIT = 64

def _truncate_obj(obj):
    """Truncate objects for use in validation tracebacks

    Cell and output lists are squashed, as are long strings, lists, and dicts.
    """
    if isinstance(obj, dict):
        truncated = { k:_truncate_obj(v) for k,v in list(obj.items())[:_ITEM_LIMIT] }
        if isinstance(truncated.get('cells'), list):
            truncated['cells'] = ['...%i cells...' % len(obj['cells'])]
        if isinstance(truncated.get('outputs'), list):
            truncated['outputs'] = ['...%i outputs...' % len(obj['outputs'])]

        if len(obj) > _ITEM_LIMIT:
            truncated['...'] = '%i keys truncated' % (len(obj) - _ITEM_LIMIT)
        return truncated
    elif isinstance(obj, list):
        truncated = [ _truncate_obj(item) for item in obj[:_ITEM_LIMIT] ]
        if len(obj) > _ITEM_LIMIT:
            truncated.append('...%i items truncated...' % (len(obj) - _ITEM_LIMIT))
        return truncated
    elif isinstance(obj, str):
        truncated = obj[:_STR_LIMIT]
        if len(obj) > _STR_LIMIT:
            truncated += '...'
        return truncated
    else:
        return obj

class NotebookValidationError(ValidationError):
    """Schema ValidationError with truncated representation

    to avoid massive verbose tracebacks.
    """
    def __init__(self, original, ref=None):
        self.original = original
        self.ref = getattr(self.original, 'ref', ref)
        self.message = self.original.message

    def __getattr__(self, key):
        return getattr(self.original, key)

    def __unicode__(self):
        """Custom str for validation errors

        avoids dumping full schema and notebook to logs
        """
        error = self.original
        instance = _truncate_obj(error.instance)

        return u'\n'.join([
            error.message,
            u'',
            u"Failed validating %r in %s%s:" % (
                error.validator,
                self.ref or 'notebook',
                _format_as_index(list(error.relative_schema_path)[:-1])),
            u'',
            u'On instance%s:' % _format_as_index(error.relative_path),
            pprint.pformat(instance, width=78),
        ])

    if sys.version_info >= (3,):
        __str__ = __unicode__

def better_validation_error(error, version, version_minor):
    """Get better ValidationError on oneOf failures

    oneOf errors aren't informative.
    if it's a cell type or output_type error,
    try validating directly based on the type for a better error message
    """
    key = error.schema_path[-1]
    ref = None
    if key.endswith('Of'):

        if isinstance(error.instance, dict):
            if 'cell_type' in error.instance:
                ref = error.instance['cell_type'] + "_cell"
            elif 'output_type' in error.instance:
                ref = error.instance['output_type']

        if ref:
            try:
                validate(error.instance,
                    ref,
                    version=version,
                    version_minor=version_minor,
                )
            except ValidationError as sub_error:
                # keep extending relative path
                error.relative_path.extend(sub_error.relative_path)
                sub_error.relative_path = error.relative_path
                better = better_validation_error(sub_error, version, version_minor)
                if better.ref is None:
                    better.ref = ref
                return better
            except Exception:
                # if it fails for some reason,
                # let the original error through
                pass
    return NotebookValidationError(error, ref)


def validate(nbjson, ref=None, version=None, version_minor=None, relax_add_props=False):
    """Checks whether the given notebook JSON conforms to the current
    notebook format schema.

    Raises ValidationError if not valid.
    """
    if version is None:
        from .reader import get_version
        (version, version_minor) = get_version(nbjson)

    validator = get_validator(version, version_minor, relax_add_props=relax_add_props)

    if validator is None:
        # no validator
        warnings.warn("No schema for validating v%s notebooks" % version, UserWarning)
        return

    try:
        if ref:
            return validator.validate(nbjson, {'$ref' : '#/definitions/%s' % ref})
        else:
            return validator.validate(nbjson)
    except ValidationError as e:
        raise better_validation_error(e, version, version_minor)

