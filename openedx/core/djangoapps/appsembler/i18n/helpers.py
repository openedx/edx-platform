import json

from django.template import Template, Context, Engine
from django.utils import translation
from django.utils.translation import gettext
from xblock.core import XBlock
from xmodule.modulestore.django import ModuleI18nService


class XBlockImitator:
    """
    A simple object that acts like other xblocks.
    """
    def __init__(self, name):
        # Allow `ModuleI18nService` to load the right XBlock class
        self.unmixed_class = XBlock.load_class(name)


def translate(lang, source_text):
    with translation.override(lang):
        return gettext(source_text)


def xblock_translate(xblock_name, lang, source_text):
    """
    Translates a text from both platform and XBlock translations po/mo files.

    Every xblock comes with it's own translations, so this may produce different
    translations for the same source text when used on different xblocks.
    """
    block = XBlockImitator(xblock_name)
    engine = Engine(libraries={
        'i18n': 'xblockutils.templatetags.i18n',
    })

    with translation.override(lang):
        i18n_service = ModuleI18nService(block=block)
        template_content = '{% load i18n %} {% trans %s %}'.replace(
            '%s', json.dumps(source_text)
        )
        template = Template(template_content, engine=engine)
        context = Context({'source_text': source_text, '_i18n_service': i18n_service})
        return template.render(context)
