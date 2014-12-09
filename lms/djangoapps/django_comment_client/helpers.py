from django.conf import settings
from mako.template import Template

import os


def include_mustache_templates():
    mustache_dir = settings.PROJECT_ROOT / 'templates' / 'discussion' / 'mustache'

    def is_valid_file_name(file_name):
        return file_name.endswith('.mustache')

    def read_file(file_name):
        return open(mustache_dir / file_name, "r").read().decode('utf-8')

    def template_id_from_file_name(file_name):
        return file_name.rpartition('.')[0]

    def process_mako(template_content):
        return Template(template_content).render_unicode()

    def make_script_tag(id, content):
        return u"<script type='text/template' id='{0}'>{1}</script>".format(id, content)

    return u'\n'.join(
        make_script_tag(template_id_from_file_name(file_name), process_mako(read_file(file_name)))
        for file_name in os.listdir(mustache_dir)
        if is_valid_file_name(file_name)
    )
