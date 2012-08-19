from django import forms
from django.forms.util import flatatt
from django.utils.encoding import force_unicode
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe

from wiki.editors.base import BaseEditor
from wiki.editors.markitup import MarkItUpAdminWidget

class CodeMirrorWidget(forms.Widget):
    def __init__(self, attrs=None):
        # The 'rows' and 'cols' attributes are required for HTML correctness.
        default_attrs = {'class': 'markItUp',
                         'rows': '10', 'cols': '40',}
        if attrs:
            default_attrs.update(attrs)
        super(CodeMirrorWidget, self).__init__(default_attrs)
    
    def render(self, name, value, attrs=None):
        if value is None: value = ''
        final_attrs = self.build_attrs(attrs, name=name)
        return mark_safe(u'<div><textarea%s>%s</textarea></div>' % (flatatt(final_attrs),
                conditional_escape(force_unicode(value))))


class CodeMirror(BaseEditor):
    editor_id = 'codemirror'
    
    def get_admin_widget(self, instance=None):
        return MarkItUpAdminWidget()
    
    def get_widget(self, instance=None):
        return CodeMirrorWidget()

    class AdminMedia:
        css = {
            'all': ("wiki/markitup/skins/simple/style.css",
                    "wiki/markitup/sets/admin/style.css",)
        }
        js = ("wiki/markitup/admin.init.js",
              "wiki/markitup/jquery.markitup.js",
              "wiki/markitup/sets/admin/set.js",
              )

    class Media:
        css = {
            'all': ("js/vendor/CodeMirror/codemirror.css",)
        }
        js = ("js/vendor/CodeMirror/codemirror.js",
              "js/vendor/CodeMirror/xml.js",
              "js/vendor/CodeMirror/mitx_markdown.js",
              "js/wiki/CodeMirror.init.js",
              )

