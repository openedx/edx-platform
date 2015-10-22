"""
Utils for Labster LTI Passport.
"""
import logging
from urlparse import urlparse

from django.utils.translation import ugettext as _


log = logging.getLogger(__name__)
WILD_CARD = '*'


class LtiPassportError(Exception):
    """
    This exception is raised in the case where Lti Passport is incorrect.
    """
    pass


class LtiPassport(object):
    """
    Works with lti passports.
    """
    slots = ['lti_id', 'consumer_key', 'secret_key']

    def __init__(self, passport_str):
        self.lti_id, self.consumer_key, self.secret_key = self.parse(passport_str)

    @classmethod
    def parse(cls, passport_str):
        """
        Parses a `passport_str (str)` and retuns lti_id, consumer key, secret key.
        """
        try:
            return tuple(i.strip() for i in passport_str.split(':'))
        except ValueError:
            msg = _('Could not parse LTI passport: {lti_passport}. Should be "id:key:secret" string.').format(
                lti_passport='{0!r}'.format(passport_str)
            )
            raise LtiPassportError(msg)

    @staticmethod
    def construct(lti_id, consumer_key, secret_key):
        """
        Contructs lti passport.
        """
        return ':'.join([lti_id, consumer_key, secret_key])

    def as_dict(self):
        return dict((prop, getattr(self, prop, None)) for prop in self.slots)

    def __str__(self):
        return LtiPassport.construct(self.lti_id, self.consumer_key, self.secret_key)

    def __unicode__(self):
        return unicode(str(self))


def get_simulation_id(uri):
    """
    Returns Simulation id extracted from the passed URI.
    """
    return urlparse(uri).path.strip('/').split('/')[-1]


def get_parent_unit(xblock):
    """
    Find a parent for the xblock.
    """
    while xblock:
        xblock = xblock.get_parent()
        if xblock is None:
            return None
        parent = xblock.get_parent()
        if parent is None:
            return None
        if parent.category == 'sequential':
            return xblock


class XBlockInfo(object):
    def __init__(self, info=None):
        self.is_hidden = info.is_hidden if info else True
        self.children = list(info.children) if info else []

    def set_visibility(self, value):
        if self.is_hidden is not False:
            self.is_hidden = value


def get_xblock_info(xblock, course_info, is_hidden=True, child=None):
    """
    Returns information (`is_hidden`(bool), `children`(list)) about the xblock.
    """
    info = XBlockInfo(course_info.get(xblock))
    info.set_visibility(is_hidden)
    if child is not None:
        info.children.append(child)
    return info


def course_tree_info(store, simulations, licensed_simulations):
    """
    Retuns information about the course's xblocks.
    """
    course_info = {}
    for simulation in simulations:
        simulation_id = get_simulation_id(simulation.launch_url)
        if WILD_CARD in licensed_simulations:
            is_hidden = False
        else:
            is_hidden = simulation_id not in licensed_simulations

        unit = get_parent_unit(simulation)
        if unit is None:
            log.debug('Cannot find ancestor for the xblock: %s', simulation)
            continue
        course_info[unit] = get_xblock_info(unit, course_info, is_hidden=is_hidden)
        subsection = unit.get_parent()
        if subsection is None:
            log.debug('Cannot find ancestor for the xblock: %s', unit)
            continue
        course_info[subsection] = get_xblock_info(subsection, course_info, is_hidden=is_hidden, child=unit)
        chapter = subsection.get_parent()
        if chapter is None:
            log.debug('Cannot find ancestor for the xblock: %s', subsection)
            continue
        course_info[chapter] = get_xblock_info(chapter, course_info, is_hidden=is_hidden, child=subsection)

    chapters = filter(lambda x: getattr(x, 'category') == 'chapter', course_info.keys())
    return (course_info, chapters)
