from jinja2.ext import Extension

from waffle import flag_is_active, sample_is_active, switch_is_active
from waffle.views import _generate_waffle_js


try:
    from jinja2 import pass_context
except ImportError:
    # NOTE: We can get rid of this when we stop supporting Jinja2 < 3.
    from jinja2 import contextfunction as pass_context


@pass_context
def flag_helper(context, flag_name):
    return flag_is_active(context['request'], flag_name)


@pass_context
def inline_wafflejs_helper(context):
    return _generate_waffle_js(context['request'])


class WaffleExtension(Extension):
    def __init__(self, environment):
        environment.globals['waffle'] = {
            'flag': flag_helper,
            'switch': switch_is_active,
            'sample': sample_is_active,
            'wafflejs': inline_wafflejs_helper
        }
