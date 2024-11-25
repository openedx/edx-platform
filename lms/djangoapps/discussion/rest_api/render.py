"""
Content rendering functionality

Note that this module is designed to imitate the front end behavior as
implemented in Markdown.Sanitizer.js.
"""
<<<<<<< HEAD
import bleach
import markdown

ALLOWED_TAGS = bleach.ALLOWED_TAGS | {
    'br', 'dd', 'del', 'dl', 'dt', 'h1', 'h2', 'h3', 'h4', 'hr', 'img', 'kbd', 'p', 'pre', 's',
    'strike', 'sub', 'sup', 'table', 'thead', 'th', 'tbody', 'tr', 'td', 'tfoot'
}
ALLOWED_PROTOCOLS = {"http", "https", "ftp", "mailto"}
ALLOWED_ATTRIBUTES = {
    "a": ["href", "title", "target", "rel"],
    "img": ["src", "alt", "title", "width", "height"],
=======
import nh3
import markdown

ALLOWED_TAGS = nh3.ALLOWED_TAGS | {
    'br', 'dd', 'del', 'dl', 'dt', 'h1', 'h2', 'h3', 'h4', 'hr', 'img', 'kbd', 'p', 'pre', 's',
    'strike', 'sub', 'sup', 'table', 'thead', 'th', 'tbody', 'tr', 'td', 'tfoot'
}
ALLOWED_ATTRIBUTES = {
    "a": {"href", "title", "target", "rel"},
    "img": {"src", "alt", "title", "width", "height"},
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374
}


def render_body(raw_body):
    """
    Render raw_body to HTML.

    This includes the following steps:

    * Convert Markdown to HTML
<<<<<<< HEAD
    * Sanitise HTML using bleach
=======
    * Sanitise HTML using nh3
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374

    Note that this does not prevent Markdown syntax inside a MathJax block from
    being processed, which the forums JavaScript code does.
    """
    rendered_html = markdown.markdown(raw_body)
<<<<<<< HEAD
    sanitised_html = bleach.clean(
        rendered_html,
        tags=ALLOWED_TAGS,
        protocols=ALLOWED_PROTOCOLS,
        strip=True,
        attributes=ALLOWED_ATTRIBUTES
=======
    sanitised_html = nh3.clean(
        rendered_html,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        link_rel=None,
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374
    )
    return sanitised_html
