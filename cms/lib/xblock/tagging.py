"""
Structured Tagging based on XBlockAsides
"""

from xblock.core import XBlockAside, XBlock
from xblock.fragment import Fragment
from xblock.fields import Scope, Dict
from xmodule.x_module import STUDENT_VIEW
from xmodule.capa_module import CapaModule
from abc import ABCMeta, abstractproperty
from edxmako.shortcuts import render_to_string
from django.conf import settings
from webob import Response
from collections import OrderedDict


_ = lambda text: text


class AbstractTag(object):
    """
    Abstract class for tags
    """
    __metaclass__ = ABCMeta

    @abstractproperty
    def key(self):
        """
        Subclasses must implement key
        """
        raise NotImplementedError('Subclasses must implement key')

    @abstractproperty
    def name(self):
        """
        Subclasses must implement name
        """
        raise NotImplementedError('Subclasses must implement name')

    @abstractproperty
    def allowed_values(self):
        """
        Subclasses must implement allowed_values
        """
        raise NotImplementedError('Subclasses must implement allowed_values')


class DifficultyTag(AbstractTag):
    """
    Particular implementation tags for difficulty
    """
    @property
    def key(self):
        """ Identifier for the difficulty selector """
        return 'difficulty_tag'

    @property
    def name(self):
        """ Label for the difficulty selector """
        return _('Difficulty')

    @property
    def allowed_values(self):
        """ Allowed values for the difficulty selector """
        return OrderedDict([('easy', 'Easy'), ('medium', 'Medium'), ('hard', 'Hard')])


class StructuredTagsAside(XBlockAside):
    """
    Aside that allows tagging blocks
    """
    saved_tags = Dict(help=_("Dictionary with the available tags"),
                      scope=Scope.content,
                      default={},)
    available_tags = [DifficultyTag()]

    def _get_studio_resource_url(self, relative_url):
        """
        Returns the Studio URL to a static resource.
        """
        return settings.STATIC_URL + relative_url

    @XBlockAside.aside_for(STUDENT_VIEW)
    def student_view_aside(self, block, context):  # pylint: disable=unused-argument
        """
        Display the tag selector with specific categories and allowed values,
        depending on the context.
        """
        if isinstance(block, CapaModule):
            tags = []
            for tag in self.available_tags:
                tags.append({
                    'key': tag.key,
                    'title': tag.name,
                    'values': tag.allowed_values,
                    'current_value': self.saved_tags.get(tag.key, None),
                })
            fragment = Fragment(render_to_string('structured_tags_block.html', {'tags': tags}))
            fragment.add_javascript_url(self._get_studio_resource_url('/js/xblock_asides/structured_tags.js'))
            fragment.initialize_js('StructuredTagsInit')
            return fragment
        else:
            return Fragment(u'')

    @XBlock.handler
    def save_tags(self, request=None, suffix=None):  # pylint: disable=unused-argument
        """
        Handler to save choosen tags with connected XBlock
        """
        found = False
        if 'tag' not in request.params:
            return Response("The required parameter 'tag' is not passed", status=400)

        tag = request.params['tag'].split(':')

        for av_tag in self.available_tags:
            if av_tag.key == tag[0]:
                if tag[1] in av_tag.allowed_values:
                    self.saved_tags[tag[0]] = tag[1]
                    found = True
                elif tag[1] == '':
                    self.saved_tags[tag[0]] = None
                    found = True

        if not found:
            return Response("Invalid 'tag' parameter", status=400)

        return Response()
