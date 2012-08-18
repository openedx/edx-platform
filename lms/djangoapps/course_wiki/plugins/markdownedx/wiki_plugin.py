# -*- coding: utf-8 -*-

from django.core.urlresolvers import reverse_lazy

from wiki.core import plugins_registry, baseplugin
import wiki

from course_wiki.plugins.markdownedx import mdx_circuit, mdx_wikipath, mdx_mathjax, mdx_video

class ExtendMarkdownPlugin(baseplugin.BasePlugin):
    """
    This plugin simply loads all of the markdown extensions we use in edX.
    """
    
    wiki_base_url = reverse_lazy("wiki:get", kwargs={'path' : ""})
    
    markdown_extensions = [mdx_circuit.CircuitExtension(configs={}),
                           #mdx_image.ImageExtension() , #This one doesn't work. Tries to import simplewiki.settings
                           mdx_wikipath.WikiPathExtension(configs={'base_url' : wiki_base_url}.iteritems() ) ,
                           mdx_mathjax.MathJaxExtension(configs={}) ,
                           mdx_video.VideoExtension(configs={})]

plugins_registry.register(ExtendMarkdownPlugin)

