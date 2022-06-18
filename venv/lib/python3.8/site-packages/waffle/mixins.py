from functools import partial

from django.http import Http404

from waffle import switch_is_active, flag_is_active, sample_is_active


class BaseWaffleMixin(object):

    def validate_waffle(self, waffle, func):
        if waffle.startswith('!'):
            active = not func(waffle[1:])
        else:
            active = func(waffle)
        return active

    def invalid_waffle(self):
        raise Http404('Inactive waffle')


class WaffleFlagMixin(BaseWaffleMixin):
    """
    Checks that as flag is active, or 404. Operates like the FBV decorator
    waffle_flag
    """

    waffle_flag = None

    def dispatch(self, request, *args, **kwargs):
        func = partial(flag_is_active, request)
        active = self.validate_waffle(self.waffle_flag, func)

        if not active:
            return self.invalid_waffle()

        return super(WaffleFlagMixin, self).dispatch(request, *args, **kwargs)


class WaffleSampleMixin(BaseWaffleMixin):
    """
    Checks that as switch is active, or 404. Operates like the FBV decorator
    waffle_sample.
    """

    waffle_sample = None

    def dispatch(self, request, *args, **kwargs):
        active = self.validate_waffle(self.waffle_sample, sample_is_active)

        if not active:
            return self.invalid_waffle()

        return super(WaffleSampleMixin, self).dispatch(request, *args, **kwargs)


class WaffleSwitchMixin(BaseWaffleMixin):
    """
    Checks that as switch is active, or 404. Operates like the FBV decorator
    waffle_switch.
    """

    waffle_switch = None

    def dispatch(self, request, *args, **kwargs):
        active = self.validate_waffle(self.waffle_switch, switch_is_active)

        if not active:
            return self.invalid_waffle()

        return super(WaffleSwitchMixin, self).dispatch(request, *args, **kwargs)
