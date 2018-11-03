"""
Makes the Fragment class available through the old namespace location.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

import warnings

import web_fragments.fragment


class Fragment(web_fragments.fragment.Fragment):
    """
    A wrapper around web_fragments.fragment.Fragment that provides
    backwards compatibility for the old location.

    Deprecated.
    """
    def __init__(self, *args, **kwargs):
        warnings.warn(
            'xblock.fragment is deprecated. Please use web_fragments.fragment instead',
            DeprecationWarning,
            stacklevel=2
        )
        super(Fragment, self).__init__(*args, **kwargs)

    # Provide older names for renamed methods
    add_frag_resources = web_fragments.fragment.Fragment.add_fragment_resources
    add_frags_resources = web_fragments.fragment.Fragment.add_resources
