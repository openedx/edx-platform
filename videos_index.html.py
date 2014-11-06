# -*- coding:utf-8 -*-
from mako import runtime, filters, cache
UNDEFINED = runtime.UNDEFINED
__M_dict_builtin = dict
__M_locals_builtin = locals
_magic_number = 9
_modified_time = 1415222698.315233
_enable_loop = True
_template_filename = u'/edx/app/edxapp/edx-platform/cms/templates/videos_index.html'
_template_uri = 'videos_index.html'
_source_encoding = 'utf-8'
_exports = [u'view_alerts', u'bodyclass', u'title', 'online_help_token', u'content', u'header_extras', u'requirejs']


# SOURCE LINE 3

from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _


def _mako_get_namespace(context, name):
    try:
        return context.namespaces[(__name__, name)]
    except KeyError:
        _mako_generate_namespaces(context)
        return context.namespaces[(__name__, name)]
def _mako_generate_namespaces(context):
    # SOURCE LINE 10
    ns = runtime.TemplateNamespace(u'static', context._clean_inheritance_tokens(), templateuri=u'static_content.html', callables=None,  calling_uri=_template_uri)
    context.namespaces[(__name__, u'static')] = ns

def _mako_inherit(template, context):
    _mako_generate_namespaces(context)
    return runtime._inherit_from(context, u'base.html', _template_uri)
def render_body(context,**pageargs):
    __M_caller = context.caller_stack._push_frame()
    try:
        __M_locals = __M_dict_builtin(pageargs=pageargs)
        def view_alerts():
            return render_view_alerts(context._locals(__M_locals))
        def bodyclass():
            return render_bodyclass(context._locals(__M_locals))
        def title():
            return render_title(context._locals(__M_locals))
        def online_help_token():
            return render_online_help_token(context._locals(__M_locals))
        def content():
            return render_content(context._locals(__M_locals))
        get_online_help_info = context.get('get_online_help_info', UNDEFINED)
        static = _mako_get_namespace(context, 'static')
        def header_extras():
            return render_header_extras(context._locals(__M_locals))
        def requirejs():
            return render_requirejs(context._locals(__M_locals))
        asset_callback_url = context.get('asset_callback_url', UNDEFINED)
        __M_writer = context.writer()
        # SOURCE LINE 1
        __M_writer(u'\n')
        # SOURCE LINE 2
        __M_writer(u'\n')
        # SOURCE LINE 6
        __M_writer(u'\n')
        if 'parent' not in context._data or not hasattr(context._data['parent'], 'title'):
            context['self'].title(**pageargs)
        

        # SOURCE LINE 7
        __M_writer(u'\n')
        if 'parent' not in context._data or not hasattr(context._data['parent'], 'bodyclass'):
            context['self'].bodyclass(**pageargs)
        

        # SOURCE LINE 8
        __M_writer(u'\n\n')
        # SOURCE LINE 10
        __M_writer(u'\n\n')
        if 'parent' not in context._data or not hasattr(context._data['parent'], 'header_extras'):
            context['self'].header_extras(**pageargs)
        

        # SOURCE LINE 18
        __M_writer(u'\n\n')
        if 'parent' not in context._data or not hasattr(context._data['parent'], 'requirejs'):
            context['self'].requirejs(**pageargs)
        

        # SOURCE LINE 24
        __M_writer(u'\n\n')
        if 'parent' not in context._data or not hasattr(context._data['parent'], 'content'):
            context['self'].content(**pageargs)
        

        # SOURCE LINE 102
        __M_writer(u'\n\n')
        if 'parent' not in context._data or not hasattr(context._data['parent'], 'view_alerts'):
            context['self'].view_alerts(**pageargs)
        

        # SOURCE LINE 120
        __M_writer(u'\n')
        return ''
    finally:
        context.caller_stack._pop_frame()


def render_view_alerts(context,**pageargs):
    __M_caller = context.caller_stack._push_frame()
    try:
        def view_alerts():
            return render_view_alerts(context)
        __M_writer = context.writer()
        # SOURCE LINE 104
        __M_writer(u'\n<!-- alert: save confirmed with close -->\n<div class="wrapper wrapper-alert wrapper-alert-confirmation" role="status">\n    <div class="alert confirmation">\n        <i class="icon-ok"></i>\n\n        <div class="copy">\n            <h2 class="title title-3">')
        # SOURCE LINE 111
        __M_writer(filters.decode.utf8(_('Your file has been deleted.')))
        __M_writer(u'</h2>\n        </div>\n\n        <a href="" rel="view" class="action action-alert-close">\n            <i class="icon-remove-sign"></i>\n            <span class="label">')
        # SOURCE LINE 116
        __M_writer(filters.decode.utf8(_('close alert')))
        __M_writer(u'</span>\n        </a>\n    </div>\n</div>\n')
        return ''
    finally:
        context.caller_stack._pop_frame()


def render_bodyclass(context,**pageargs):
    __M_caller = context.caller_stack._push_frame()
    try:
        def bodyclass():
            return render_bodyclass(context)
        __M_writer = context.writer()
        # SOURCE LINE 8
        __M_writer(u'is-signedin course uploads view-uploads')
        return ''
    finally:
        context.caller_stack._pop_frame()


def render_title(context,**pageargs):
    __M_caller = context.caller_stack._push_frame()
    try:
        def title():
            return render_title(context)
        __M_writer = context.writer()
        # SOURCE LINE 7
        __M_writer(filters.decode.utf8(_("Files &amp; Uploads")))
        return ''
    finally:
        context.caller_stack._pop_frame()


def render_online_help_token(context):
    __M_caller = context.caller_stack._push_frame()
    try:
        __M_writer = context.writer()
        # SOURCE LINE 2
        return "videos" 
        
        return ''
    finally:
        context.caller_stack._pop_frame()


def render_content(context,**pageargs):
    __M_caller = context.caller_stack._push_frame()
    try:
        def content():
            return render_content(context)
        get_online_help_info = context.get('get_online_help_info', UNDEFINED)
        asset_callback_url = context.get('asset_callback_url', UNDEFINED)
        def online_help_token():
            return render_online_help_token(context)
        __M_writer = context.writer()
        # SOURCE LINE 26
        __M_writer(u'\n\n<div class="wrapper-mast wrapper">\n    <header class="mast has-actions has-subtitle">\n        <h1 class="page-header">\n            <small class="subtitle">')
        # SOURCE LINE 31
        __M_writer(filters.decode.utf8(_("Content")))
        __M_writer(u'</small>\n            <span class="sr">&gt; </span>')
        # SOURCE LINE 32
        __M_writer(filters.decode.utf8(_("Files &amp; Uploads")))
        __M_writer(u'\n        </h1>\n\n        <nav class="nav-actions">\n            <h3 class="sr">')
        # SOURCE LINE 36
        __M_writer(filters.decode.utf8(_("Page Actions")))
        __M_writer(u'</h3>\n            <ul>\n                <li class="nav-item">\n                    <a href="#" class="button upload-button new-button"><i class="icon-plus"></i> ')
        # SOURCE LINE 39
        __M_writer(filters.decode.utf8(_("Upload New File")))
        __M_writer(u'</a>\n                </li>\n            </ul>\n        </nav>\n    </header>\n</div>\n\n<div class="wrapper-content wrapper">\n    <section class="content">\n        <article class="content-primary" role="main">\n            <div class="assets-wrapper"/>\n            <div class="ui-loading">\n                <p><span class="spin"><i class="icon-refresh"></i></span> <span class="copy">')
        # SOURCE LINE 51
        __M_writer(filters.decode.utf8(_("Loading&hellip;")))
        __M_writer(u'</span></p>\n            </div>\n        </article>\n\n        <aside class="content-supplementary" role="complimentary">\n            <div class="bit">\n                <h3 class="title-3">')
        # SOURCE LINE 57
        __M_writer(filters.decode.utf8(_("Adding Files for Your Course")))
        __M_writer(u'</h3>\n\n                <p>')
        # SOURCE LINE 59
        __M_writer(filters.decode.utf8(_("To add files to use in your course, click {em_start}Upload New File{em_end}. Then follow the prompts to upload a file from your computer.").format(em_start='<strong>', em_end="</strong>")))
        __M_writer(u'</p>\n\n                <p>')
        # SOURCE LINE 61
        __M_writer(filters.decode.utf8(_("{em_start}Caution{em_end}: edX recommends that you limit the file size to {em_start}10 MB{em_end}. In addition, do not upload video or audio files. You should use a third party service to host multimedia files.").format(em_start='<strong>', em_end="</strong>")))
        __M_writer(u'</p>\n\n              <p>')
        # SOURCE LINE 63
        __M_writer(filters.decode.utf8(_("The course image, textbook chapters, and files that appear on your Course Handouts sidebar also appear in this list.")))
        __M_writer(u'</p>\n            </div>\n            <div class="bit">\n                <h3 class="title-3">')
        # SOURCE LINE 66
        __M_writer(filters.decode.utf8(_("Using File URLs")))
        __M_writer(u'</h3>\n\n                <p>')
        # SOURCE LINE 68
        __M_writer(filters.decode.utf8(_("Use the {em_start}Embed URL{em_end} value to link to the file or image from a component, a course update, or a course handout.").format(em_start='<strong>', em_end="</strong>")))
        __M_writer(u'</p>\n\n                <p>')
        # SOURCE LINE 70
        __M_writer(filters.decode.utf8(_("Use the {em_start}External URL{em_end} value to reference the file or image only from outside of your course.").format(em_start='<strong>', em_end="</strong>")))
        __M_writer(u'</p>\n                <p>')
        # SOURCE LINE 71
        __M_writer(filters.decode.utf8(_("Click in the Embed URL or External URL column to select the value, then copy it.")))
        __M_writer(u'</p>\n            </div>\n            <div class="bit external-help">\n                <a href="')
        # SOURCE LINE 74
        __M_writer(filters.decode.utf8(get_online_help_info(online_help_token())['doc_url']))
        __M_writer(u'" target="_blank" class="button external-help-button">')
        __M_writer(filters.decode.utf8(_("Learn more about managing files")))
        __M_writer(u'</a>\n            </div>\n\n        </aside>\n    </section>\n</div>\n\n<div class="upload-modal modal">\n    <a href="#" class="close-button"><i class="icon-remove-sign"></i> <span class="sr">')
        # SOURCE LINE 82
        __M_writer(filters.decode.utf8(_('close')))
        __M_writer(u'</span></a>\n    <div class="modal-body">\n        <h1 class="title">')
        # SOURCE LINE 84
        __M_writer(filters.decode.utf8(_("Upload New File")))
        __M_writer(u'</h1>\n        <p class="file-name">\n        <div class="progress-bar">\n            <div class="progress-fill"></div>\n        </div>\n        <div class="embeddable">\n            <label>URL:</label>\n            <input type="text" class="embeddable-xml-input" value=\'\' readonly>\n        </div>\n        <form class="file-chooser" action="')
        # SOURCE LINE 93
        __M_writer(filters.decode.utf8(asset_callback_url))
        __M_writer(u'"\n              method="post" enctype="multipart/form-data">\n            <a href="#" class="choose-file-button">')
        # SOURCE LINE 95
        __M_writer(filters.decode.utf8(_("Choose File")))
        __M_writer(u'</a>\n            <input type="file" class="file-input" name="file" multiple>\n        </form>\n    </div>\n</div>\n\n\n')
        return ''
    finally:
        context.caller_stack._pop_frame()


def render_header_extras(context,**pageargs):
    __M_caller = context.caller_stack._push_frame()
    try:
        def header_extras():
            return render_header_extras(context)
        static = _mako_get_namespace(context, 'static')
        __M_writer = context.writer()
        # SOURCE LINE 12
        __M_writer(u'\n')
        # SOURCE LINE 13
        for template_name in ["asset-library", "asset", "paging-header", "paging-footer"]:
            # SOURCE LINE 14
            __M_writer(u'<script type="text/template" id="')
            __M_writer(filters.decode.utf8(template_name))
            __M_writer(u'-tpl">\n    ')
            def ccall(caller):
                def body():
                    __M_writer = context.writer()
                    return ''
                return [body]
            context.caller_stack.nextcaller = runtime.Namespace('caller', context, callables=ccall(__M_caller))
            try:
                # SOURCE LINE 15
                __M_writer(filters.decode.utf8(static.include(path=u'js/' + (template_name) + u'.underscore')))
            finally:
                context.caller_stack.nextcaller = None
            __M_writer(u'\n</script>\n')
        return ''
    finally:
        context.caller_stack._pop_frame()


def render_requirejs(context,**pageargs):
    __M_caller = context.caller_stack._push_frame()
    try:
        def requirejs():
            return render_requirejs(context)
        asset_callback_url = context.get('asset_callback_url', UNDEFINED)
        __M_writer = context.writer()
        # SOURCE LINE 20
        __M_writer(u'\n    require(["js/factories/asset_index"], function (AssetIndexFactory) {\n        AssetIndexFactory("')
        # SOURCE LINE 22
        __M_writer(filters.decode.utf8(asset_callback_url))
        __M_writer(u'");\n    });\n')
        return ''
    finally:
        context.caller_stack._pop_frame()


