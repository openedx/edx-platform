"""
This has custom renderers: classes that know how to render certain problem tags (e.g. <math> and
<solution>) to html.

These tags do not have state, so they just get passed the system (for access to render_template),
and the xml element.
"""

from .registry import TagRegistry

import logging
import re

from lxml import etree
import xml.sax.saxutils as saxutils
from .registry import TagRegistry

log = logging.getLogger(__name__)

registry = TagRegistry()

#-----------------------------------------------------------------------------


class MathRenderer(object):
    tags = ['math']

    def __init__(self, system, xml):
        r"""
        Render math using latex-like formatting.

        Examples:

        <math>$\displaystyle U(r)=4 U_0 $</math>
        <math>$r_0$</math>

        We convert these to [mathjax]...[/mathjax] and [mathjaxinline]...[/mathjaxinline]

        TODO: use shorter tags (but this will require converting problem XML files!)
        """
        self.system = system
        self.xml = xml

        mathstr = re.sub(r'\$(.*)\$', r'[mathjaxinline]\1[/mathjaxinline]', xml.text)
        mtag = 'mathjax'
        if not r'\displaystyle' in mathstr:
            mtag += 'inline'
        else:
            mathstr = mathstr.replace(r'\displaystyle', '')
        self.mathstr = mathstr.replace('mathjaxinline]', '%s]' % mtag)


    def get_html(self):
        """
        Return the contents of this tag, rendered to html, as an etree element.
        """
        # TODO: why are there nested html tags here??  Why are there html tags at all, in fact?
        html = '<html><html>%s</html><html>%s</html></html>' % (
            self.mathstr, saxutils.escape(self.xml.tail))
        try:
            xhtml = etree.XML(html)
        except Exception as err:
            if self.system.DEBUG:
                msg = '<html><div class="inline-error"><p>Error %s</p>' % (
                    str(err).replace('<', '&lt;'))
                msg += ('<p>Failed to construct math expression from <pre>%s</pre></p>' %
                        html.replace('<', '&lt;'))
                msg += "</div></html>"
                log.error(msg)
                return etree.XML(msg)
            else:
                raise
        return xhtml


registry.register(MathRenderer)

#-----------------------------------------------------------------------------


class SolutionRenderer(object):
    """
    A solution is just a <span>...</span> which is given an ID, that is used for displaying an
    extended answer (a problem "solution") after "show answers" is pressed.

    Note that the solution content is NOT rendered and returned in the HTML. It is obtained by an
    ajax call.
    """
    tags = ['solution']

    def __init__(self, system, xml):
        self.system = system
        self.id = xml.get('id')

    def get_html(self):
        context = {'id': self.id}
        html = self.system.render_template("solutionspan.html", context)
        return etree.XML(html)

registry.register(SolutionRenderer)

#-----------------------------------------------------------------------------


class TargetedFeedbackRenderer(object):
    '''
    A targeted feedback is just a <span>...</span> that is used for displaying an
    extended piece of feedback to students if they incorrectly answered a question.
    '''
    tags = ['targetedfeedback']

    def __init__(self, system, xml):
        self.system = system
        self.xml = xml

    def get_html(self):
        """
        Return the contents of this tag, rendered to html, as an etree element.
        """

        html = '<section class="targeted-feedback-span"><span>%s</span></section>' % (
            etree.tostring(self.xml))
        try:
            xhtml = etree.XML(html)
        except Exception as err:
            if self.system.DEBUG:
                msg = '<html><div class="inline-error"><p>Error %s</p>' % (
                    str(err).replace('<', '&lt;'))
                msg += ('<p>Failed to construct targeted feedback from <pre>%s</pre></p>' %
                        html.replace('<', '&lt;'))
                msg += "</div></html>"
                log.error(msg)
                return etree.XML(msg)
            else:
                raise
        return xhtml

registry.register(TargetedFeedbackRenderer)
