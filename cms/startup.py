"""
Module with code executed during Studio startup
"""

import django
from django.conf import settings

import cms.lib.xblock.runtime
import xmodule.x_module
from openedx.core.djangoapps.monkey_patch import django_db_models_options
from openedx.core.djangoapps.theming.core import enable_theming
from openedx.core.djangoapps.theming.helpers import is_comprehensive_theming_enabled
from openedx.core.lib.django_startup import autostartup
from openedx.core.lib.xblock_utils import xblock_local_resource_url
from openedx.core.release import doc_version
from startup_configurations.validate_config import validate_cms_config

# Force settings to run so that the python path is modified

settings.INSTALLED_APPS  # pylint: disable=pointless-statement


def run():
    """
    Executed during django startup
    """
    implicit_in_patch()

    django_db_models_options.patch()

    # Comprehensive theming needs to be set up before django startup,
    # because modifying django template paths after startup has no effect.
    if is_comprehensive_theming_enabled():
        enable_theming()

    django.setup()

    autostartup()

    add_mimetypes()

    # In order to allow descriptors to use a handler url, we need to
    # monkey-patch the x_module library.
    # TODO: Remove this code when Runtimes are no longer created by modulestores
    # https://openedx.atlassian.net/wiki/display/PLAT/Convert+from+Storage-centric+runtimes+to+Application-centric+runtimes
    xmodule.x_module.descriptor_global_handler_url = cms.lib.xblock.runtime.handler_url
    xmodule.x_module.descriptor_global_local_resource_url = xblock_local_resource_url

    # Set the version of docs that help-tokens will go to.
    settings.HELP_TOKENS_LANGUAGE_CODE = settings.LANGUAGE_CODE
    settings.HELP_TOKENS_VERSION = doc_version()

    # validate configurations on startup
    validate_cms_config(settings)


def add_mimetypes():
    """
    Add extra mimetypes. Used in xblock_resource.

    If you add a mimetype here, be sure to also add it in lms/startup.py.
    """
    import mimetypes

    mimetypes.add_type('application/vnd.ms-fontobject', '.eot')
    mimetypes.add_type('application/x-font-opentype', '.otf')
    mimetypes.add_type('application/x-font-ttf', '.ttf')
    mimetypes.add_type('application/font-woff', '.woff')

def implicit_in_patch():
    django.db.models.sql.query.Query.build_filter = build_filter_patched

from django.db.models.sql.where import (
    AND
)
def build_filter_patched(self, filter_expr, branch_negated=False, current_negated=False,
                 can_reuse=None, connector=AND, allow_joins=True, split_subq=True):
    """
    Builds a WhereNode for a single filter clause, but doesn't add it
    to this Query. Query.add_q() will then add this filter to the where
    or having Node.

    The 'branch_negated' tells us if the current branch contains any
    negations. This will be used to determine if subqueries are needed.

    The 'current_negated' is used to determine if the current filter is
    negated or not and this will be used to determine if IS NULL filtering
    is needed.

    The difference between current_netageted and branch_negated is that
    branch_negated is set on first negation, but current_negated is
    flipped for each negation.

    Note that add_filter will not do any negating itself, that is done
    upper in the code by add_q().

    The 'can_reuse' is a set of reusable joins for multijoins.

    The method will create a filter clause that can be added to the current
    query. However, if the filter isn't added to the query then the caller
    is responsible for unreffing the joins used.
    """
    import copy
    import warnings
    from collections import Iterator, Mapping, OrderedDict
    from itertools import chain, count, product
    from string import ascii_uppercase
    
    from django.core.exceptions import FieldDoesNotExist, FieldError
    from django.db import DEFAULT_DB_ALIAS, connections
    from django.db.models.aggregates import Count
    from django.db.models.constants import LOOKUP_SEP
    from django.db.models.expressions import Col, Ref
    from django.db.models.query_utils import (
        PathInfo, Q, refs_aggregate, refs_expression,
    )
    from django.db.models.sql.constants import (
        INNER, LOUTER, ORDER_DIR, ORDER_PATTERN, QUERY_TERMS, SINGLE,
    )
    from django.db.models.sql.datastructures import (
        BaseTable, Empty, EmptyResultSet, Join, MultiJoin,
    )
    from django.db.models.sql.where import (
        AND, OR, Constraint, EmptyWhere, EverythingNode, ExtraWhere, WhereNode,
    )
    from django.utils import six
    from django.utils.deprecation import (
        RemovedInDjango19Warning, RemovedInDjango110Warning,
    )
    from django.utils.encoding import force_text
    from django.utils.tree import Node

    arg, value = filter_expr
    if not arg:
        raise FieldError("Cannot parse keyword query %r" % arg)
    lookups, parts, reffed_expression = self.solve_lookup_type(arg)
    if not allow_joins and len(parts) > 1:
        raise FieldError("Joined field references are not permitted in this query")

    # Work out the lookup type and remove it from the end of 'parts',
    # if necessary.
    value, lookups, used_joins = self.prepare_lookup_value(value, lookups, can_reuse, allow_joins)

    clause = self.where_class()
    if reffed_expression:
        condition = self.build_lookup(lookups, reffed_expression, value)
        if not condition:
            # Backwards compat for custom lookups
            assert len(lookups) == 1
            condition = (reffed_expression, lookups[0], value)
        clause.add(condition, AND)
        return clause, []

    opts = self.get_meta()
    alias = self.get_initial_alias()
    allow_many = not branch_negated or not split_subq

    try:
        field, sources, opts, join_list, path = self.setup_joins(
            parts, opts, alias, can_reuse=can_reuse, allow_many=allow_many)

        # Prevent iterator from being consumed by check_related_objects()
        if isinstance(value, Iterator):
            value = list(value)
        self.check_related_objects(field, value, opts)

        # split_exclude() needs to know which joins were generated for the
        # lookup parts
        self._lookup_joins = join_list
    except MultiJoin as e:
        return self.split_exclude(filter_expr, LOOKUP_SEP.join(parts[:e.level]),
                                  can_reuse, e.names_with_path)

    if can_reuse is not None:
        can_reuse.update(join_list)
    used_joins = set(used_joins).union(set(join_list))

    # Process the join list to see if we can remove any non-needed joins from
    # the far end (fewer tables in a query is better).
    targets, alias, join_list = self.trim_joins(sources, join_list, path)

    if hasattr(field, 'get_lookup_constraint'):
        if len(lookups) == 1 and lookups[0] == 'exact':
            if hasattr(value, 'query'):
                warnings.warn(
                    "MY COMMENT: parts: {}, lookups: {}, value.query: {}".format(parts, lookups, value.query),
                    RemovedInDjango19Warning, stacklevel=2)
                raise RuntimeError("MY COMMENT: parts: {}, lookups: {}, value.query: {}".format(parts, lookups, value.query))
        # For now foreign keys get special treatment. This should be
        # refactored when composite fields lands.
        condition = field.get_lookup_constraint(self.where_class, alias, targets, sources,
                                                lookups, value)
        lookup_type = lookups[-1]
    else:
        assert(len(targets) == 1)
        if hasattr(targets[0], 'as_sql'):
            # handle Expressions as annotations
            col = targets[0]
        else:
            col = targets[0].get_col(alias, field)
        condition = self.build_lookup(lookups, col, value)
        if not condition:
            # Backwards compat for custom lookups
            if lookups[0] not in self.query_terms:
                raise FieldError(
                    "Join on field '%s' not permitted. Did you "
                    "misspell '%s' for the lookup type?" %
                    (col.output_field.name, lookups[0]))
            if len(lookups) > 1:
                raise FieldError("Nested lookup '%s' not supported." %
                                 LOOKUP_SEP.join(lookups))
            condition = (Constraint(alias, targets[0].column, field), lookups[0], value)
            lookup_type = lookups[-1]
        else:
            lookup_type = condition.lookup_name

    clause.add(condition, AND)

    require_outer = lookup_type == 'isnull' and value is True and not current_negated
    if current_negated and (lookup_type != 'isnull' or value is False):
        require_outer = True
        if (lookup_type != 'isnull' and (
                self.is_nullable(targets[0]) or
                self.alias_map[join_list[-1]].join_type == LOUTER)):
            # The condition added here will be SQL like this:
            # NOT (col IS NOT NULL), where the first NOT is added in
            # upper layers of code. The reason for addition is that if col
            # is null, then col != someval will result in SQL "unknown"
            # which isn't the same as in Python. The Python None handling
            # is wanted, and it can be gotten by
            # (col IS NULL OR col != someval)
            #   <=>
            # NOT (col IS NOT NULL AND col = someval).
            lookup_class = targets[0].get_lookup('isnull')
            clause.add(lookup_class(targets[0].get_col(alias, sources[0]), False), AND)
    return clause, used_joins if not require_outer else ()
