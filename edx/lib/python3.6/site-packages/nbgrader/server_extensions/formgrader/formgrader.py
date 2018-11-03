import os

from nbconvert.exporters import HTMLExporter
from traitlets import default
from tornado import web
from jinja2 import Environment, FileSystemLoader
from notebook.utils import url_path_join as ujoin

from . import handlers, apihandlers
from ...apps.baseapp import NbGrader


class FormgradeExtension(NbGrader):

    name = u'formgrade'
    description = u'Grade a notebook using an HTML form'

    @default("classes")
    def _classes_default(self):
        classes = super(FormgradeExtension, self)._classes_default()
        classes.append(HTMLExporter)
        return classes

    def build_extra_config(self):
        extra_config = super(FormgradeExtension, self).build_extra_config()
        extra_config.HTMLExporter.template_file = 'formgrade'
        extra_config.HTMLExporter.template_path = [handlers.template_path]
        return extra_config

    def init_tornado_settings(self, webapp):
        # Init jinja environment
        jinja_env = Environment(loader=FileSystemLoader([handlers.template_path]))

        # Configure the formgrader settings
        tornado_settings = dict(
            nbgrader_url_prefix=os.path.relpath(self.coursedir.root, self.parent.notebook_dir),
            nbgrader_coursedir=self.coursedir,
            nbgrader_exporter=HTMLExporter(config=self.config),
            nbgrader_gradebook=None,
            nbgrader_db_url=self.coursedir.db_url,
            nbgrader_jinja2_env=jinja_env,
        )

        webapp.settings.update(tornado_settings)

    def init_handlers(self, webapp):
        h = []
        h.extend(handlers.default_handlers)
        h.extend(apihandlers.default_handlers)
        h.extend([
            (r"/formgrader/static/(.*)", web.StaticFileHandler, {'path': handlers.static_path}),
            (r"/formgrader/.*", handlers.Template404)
        ])

        def rewrite(x):
            pat = ujoin(webapp.settings['base_url'], x[0].lstrip('/'))
            return (pat,) + x[1:]

        webapp.add_handlers(".*$", [rewrite(x) for x in h])

    def start(self):
        raise NotImplementedError


def load_jupyter_server_extension(nbapp):
    """Load the formgrader extension"""
    nbapp.log.info("Loading the formgrader nbgrader serverextension")
    webapp = nbapp.web_app
    formgrader = FormgradeExtension(parent=nbapp)
    formgrader.log = nbapp.log
    formgrader.initialize([])
    formgrader.init_tornado_settings(webapp)
    formgrader.init_handlers(webapp)

