"""
Template tags for handling i18n trans function on xblocks
"""
from django import template
from django.templatetags.i18n import do_translate

register = template.Library()  # pylint: disable=invalid-name


class ProxyTransNode(template.Node):
    """
    This node is a proxy of a django TranslateNode.
    In case the context has a i18n_service object, it passes the result through it
    """

    def __init__(self, do_translate_func):
        self.do_translate = do_translate_func

    def render(self, context):
        django_translated = self.do_translate.render(context)

        try:
            i18n_service = context.get('i18n_service', None)
            if i18n_service:
                return i18n_service.gettext(django_translated)
        except Exception:  # pylint: disable=broad-except
            # TODO: We could decide to log this, but for now, we will silently continue
            return django_translated
        return django_translated


def xblock_translate(parser, token):
    """
    This is a proxy implementation of the i18n `trans` tag.
    It takes the result of using the regular translate block and passes it to
    the ProxyTransNode for rendering
    """
    return ProxyTransNode(do_translate(parser, token))


register.tag('trans', xblock_translate)
