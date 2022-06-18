from django import template
from django.template.base import VariableDoesNotExist

from waffle import flag_is_active, sample_is_active, switch_is_active
from waffle.views import _generate_waffle_js


register = template.Library()


class WaffleNode(template.Node):
    child_nodelists = ('nodelist_true', 'nodelist_false')

    def __init__(self, nodelist_true, nodelist_false, condition, name,
                 compiled_name):
        self.nodelist_true = nodelist_true
        self.nodelist_false = nodelist_false
        self.condition = condition
        self.name = name
        self.compiled_name = compiled_name

    def __repr__(self):
        return '<Waffle node: %s>' % self.name

    def __iter__(self):
        for node in self.nodelist_true:
            yield node
        for node in self.nodelist_false:
            yield node

    def render(self, context):
        try:
            name = self.compiled_name.resolve(context)
        except VariableDoesNotExist:
            name = self.name
        if not name:
            name = self.name
        if self.condition(context.get('request', None), name):
            return self.nodelist_true.render(context)
        return self.nodelist_false.render(context)

    @classmethod
    def handle_token(cls, parser, token, kind, condition):
        bits = token.split_contents()
        if len(bits) < 2:
            raise template.TemplateSyntaxError("%r tag requires an argument" %
                                               bits[0])

        name = bits[1]
        compiled_name = parser.compile_filter(name)

        nodelist_true = parser.parse(('else', 'end%s' % kind))
        token = parser.next_token()
        if token.contents == 'else':
            nodelist_false = parser.parse(('end%s' % kind,))
            parser.delete_first_token()
        else:
            nodelist_false = template.NodeList()

        return cls(nodelist_true, nodelist_false, condition,
                   name, compiled_name)


@register.tag
def flag(parser, token):
    return WaffleNode.handle_token(parser, token, 'flag', flag_is_active)


@register.tag
def switch(parser, token):
    return WaffleNode.handle_token(parser, token, 'switch', lambda request, name: switch_is_active(name))


@register.tag
def sample(parser, token):
    return WaffleNode.handle_token(parser, token, 'sample', lambda request, name: sample_is_active(name))


class InlineWaffleJSNode(template.Node):
    def render(self, context):
        return _generate_waffle_js(context['request'])


@register.tag
def wafflejs(parser, token):
    return InlineWaffleJSNode()
