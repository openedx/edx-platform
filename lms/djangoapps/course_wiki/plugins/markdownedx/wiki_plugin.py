# -*- coding: utf-8 -*-

from wiki.core.plugins.base import BasePlugin
from wiki.core.plugins import registry as plugin_registry

from course_wiki.plugins.markdownedx import mdx_mathjax, mdx_video


class ExtendMarkdownPlugin(BasePlugin):
    """
    This plugin simply loads all of the markdown extensions we use in edX.
    """

    markdown_extensions = [
        mdx_mathjax.MathJaxExtension(configs={}),
        mdx_video.VideoExtension(configs={}),
    ]

plugin_registry.register(ExtendMarkdownPlugin)
