""" Constants associated with catalog """
from __future__ import absolute_import

from enum import Enum


class PathwayType(Enum):
    """ Allowed values for pathway_type. """
    CREDIT = 'credit'
    INDUSTRY = 'industry'
