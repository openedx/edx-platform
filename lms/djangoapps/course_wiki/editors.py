from django import forms
from django.forms.utils import flatatt
from django.utils.encoding import force_unicode
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe

from django.template.loader import render_to_string

from wiki.editors.base import BaseEditor
from wiki.editors.markitup import MarkItUpAdminWidget


class CodeMirrorWidget(forms.Widget):
    def __init__(self, attrs=None):
        # The 'rows' and 'cols' attributes are required for HTML correctness.
        default_attrs = {'class': 'markItUp',
                         'rows': '10', 'cols': '40', }
        if attrs:
            default_attrs.update(attrs)
        super(CodeMirrorWidget, self).__init__(default_attrs)

    def render(self, name, value, attrs=None):
        if value is None:
            value = ''

        final_attrs = self.build_attrs(attrs, name=name)

        # TODO use the help_text field of edit form instead of rendering a template

        return render_to_string('wiki/includes/editor_widget.html',
                                {'attrs': mark_safe(flatatt(final_attrs)),
                                 'content': conditional_escape(force_unicode(value)),
                                 })


class CodeMirror(BaseEditor):
    editor_id = 'codemirror'

    def get_admin_widget(self, instance=None):
        return MarkItUpAdminWidget()

    def get_widget(self, instance=None):
        return CodeMirrorWidget()

    class AdminMedia(object):  # pylint: disable=missing-docstring
        css = {
            'all': ("wiki/markitup/skins/simple/style.css",
                    "wiki/markitup/sets/admin/style.css",)
        }
        js = ("wiki/markitup/admin.init.js",
              "wiki/markitup/jquery.markitup.js",
              "wiki/markitup/sets/admin/set.js",
              )

    class Media(object):  # pylint: disable=missing-docstring
        css = {
            'all': ("js/vendor/CodeMirror/codemirror.css",)
        }
        js = ("js/vendor/CodeMirror/codemirror.js",
              "js/vendor/CodeMirror/addons/xml.js",
              "js/vendor/CodeMirror/addons/edx_markdown.js",
              "js/wiki/accessible.js",
              "js/wiki/CodeMirror.init.js",
              )
