""" Labster Course utils. """
import logging

from openedx.core.djangoapps.labster.exceptions import LtiPassportError

log = logging.getLogger(__name__)


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
