"""
This has custom renderers: classes that know how to render certain problem tags (e.g. <math> and
<solution>) to html.

These tags do not have state, so they just get passed the system (for access to render_template),
and the xml element.
"""

import logging
import re

from cgi import escape as cgi_escape
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
        if r'\displaystyle' not in mathstr:
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


class DescriptionRenderer(object):
    """
    Description provides help text for a question.
    """
    tags = ['description']

    def __init__(self, system, xml):
        self.system = system
        self.id = xml.get('id')  # pylint: disable=invalid-name
        self.text = xml.text

    def get_html(self):
        """
        Return HTML for <description> tag.
        """
        context = {'id': self.id, 'text': self.text}
        html = self.system.render_template("description.html", context)
        return etree.XML(html)

registry.register(DescriptionRenderer)

#-----------------------------------------------------------------------------


class TargetedFeedbackRenderer(object):
    """
    A targeted feedback is just a <span>...</span> that is used for displaying an
    extended piece of feedback to students if they incorrectly answered a question.
    """
    tags = ['targetedfeedback']

    def __init__(self, system, xml):
        self.system = system
        self.xml = xml

    def get_html(self):
        """
        Return the contents of this tag, rendered to html, as an etree element.
        """
        html = '<section class="targeted-feedback-span"><span>{}</span></section>'.format(etree.tostring(self.xml))
        try:
            xhtml = etree.XML(html)
        except Exception as err:  # pylint: disable=broad-except
            if self.system.DEBUG:
                msg = """
                    <html>
                      <div class="inline-error">
                        <p>Error {err}</p>
                        <p>Failed to construct targeted feedback from <pre>{html}</pre></p>
                      </div>
                    </html>
                """.format(err=cgi_escape(err), html=cgi_escape(html))
                log.error(msg)
                return etree.XML(msg)
            else:
                raise
        return xhtml

registry.register(TargetedFeedbackRenderer)

#-----------------------------------------------------------------------------


class ClarificationRenderer(object):
    """
    A clarification appears as an inline icon which reveals more information when the user
    hovers over it.

    e.g. <p>Enter the ROA <clarification>Return on Assets</clarification> for 2015:</p>
    """
    tags = ['clarification']

    def __init__(self, system, xml):
        self.system = system
        # Get any text content found inside this tag prior to the first child tag. It may be a string or None type.
        initial_text = xml.text if xml.text else ''
        self.inner_html = initial_text + ''.join(etree.tostring(element) for element in xml)
        self.tail = xml.tail

    def get_html(self):
        """
        Return the contents of this tag, rendered to html, as an etree element.
        """
        context = {'clarification': self.inner_html}
        html = self.system.render_template("clarification.html", context)
        xml = etree.XML(html)
        # We must include any text that was following our original <clarification>...</clarification> XML node.:
        xml.tail = self.tail
        return xml

registry.register(ClarificationRenderer)
