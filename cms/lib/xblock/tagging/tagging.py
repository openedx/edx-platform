# -*- coding: utf-8 -*-
"""
Structured Tagging based on XBlockAsides
"""

from xblock.core import XBlockAside, XBlock
from xblock.fragment import Fragment
from xblock.fields import Scope, Dict
from xmodule.x_module import AUTHOR_VIEW
from xmodule.capa_module import CapaModule
from edxmako.shortcuts import render_to_string
from django.conf import settings
from webob import Response
from .models import TagCategories


_ = lambda text: text


class StructuredTagsAside(XBlockAside):
    """
    Aside that allows tagging blocks
    """
    saved_tags = Dict(help=_("Dictionary with the available tags"),
                      scope=Scope.content,
                      default={},)

    def get_available_tags(self):
        """
        Return available tags
        """
        return TagCategories.objects.all()

    def _get_studio_resource_url(self, relative_url):
        """
        Returns the Studio URL to a static resource.
        """
        return settings.STATIC_URL + relative_url

    @XBlockAside.aside_for(AUTHOR_VIEW)
    def student_view_aside(self, block, context):  # pylint: disable=unused-argument
        """
        Display the tag selector with specific categories and allowed values,
        depending on the context.
        """
        if isinstance(block, CapaModule):
            tags = []
            for tag in self.get_available_tags():
                values = tag.get_values()
                current_value = self.saved_tags.get(tag.name, None)

                if current_value is not None and current_value not in values:
                    values.insert(0, current_value)

                tags.append({
                    'key': tag.name,
                    'title': tag.title,
                    'values': values,
                    'current_value': current_value
                })
            fragment = Fragment(render_to_string('structured_tags_block.html', {'tags': tags,
                                                                                'block_location': block.location}))
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

        for av_tag in self.get_available_tags():
            if av_tag.name == tag[0]:
                if tag[1] == '':
                    self.saved_tags[tag[0]] = None
                    found = True
                elif tag[1] in av_tag.get_values():
                    self.saved_tags[tag[0]] = tag[1]
                    found = True

        if not found:
            return Response("Invalid 'tag' parameter", status=400)

        return Response()

    def get_event_context(self, event_type, event):  # pylint: disable=unused-argument
        """
        This method return data that should be associated with the "check_problem" event
        """
        if self.saved_tags and event_type == "problem_check":
            return {'saved_tags': self.saved_tags}
        else:
            return None
