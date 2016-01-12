"""
Example implementation of Structured Tagging based on XBlockAsides
"""

from xblock.core import XBlockAside
from xblock.fragment import Fragment
from xblock.fields import Scope, Dict
from xmodule.x_module import STUDENT_VIEW
from xmodule.capa_module import CapaModule
from abc import ABCMeta, abstractproperty
from edxmako.shortcuts import render_to_string


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


class LearningOutcomeTag(AbstractTag):
    """
    Particular implementation tags for learning outcomes
    """
    @property
    def key(self):
        """ Identifier for the learning outcome selector """
        return 'learning_outcome_tag'

    @property
    def name(self):
        """ Label for the learning outcome selector """
        return _('Learning outcomes')

    @property
    def allowed_values(self):
        """ Allowed values for the learning outcome selector """
        return {'test1': 'Test 1', 'test2': 'Test 2', 'test3': 'Test 3'}


class StructuredTagsAside(XBlockAside):
    """
    Aside that allows tagging blocks
    """
    saved_tags = Dict(help=_("Dictionary with the available tags"),
                      scope=Scope.content,
                      default={},)
    available_tags = [LearningOutcomeTag()]

    @XBlockAside.aside_for(STUDENT_VIEW)
    def student_view_aside(self, block, context):
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
            return Fragment(render_to_string('structured_tags_block.html', {'tags': tags}))
            #return Fragment(u'<div class="xblock-render">Hello world!!!</div>')
        else:
            return Fragment(u'')
