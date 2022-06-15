"""
Content rendering functionality

Note that this module is designed to imitate the front end behavior as
implemented in Markdown.Sanitizer.js.
"""
import bleach
import markdown

ALLOWED_TAGS = bleach.ALLOWED_TAGS + [
    'br', 'dd', 'del', 'dl', 'dt', 'h1', 'h2', 'h3', 'h4', 'hr', 'img', 'kbd', 'p', 'pre', 's',
    'strike', 'sub', 'sup'
]
ALLOWED_PROTOCOLS = ["http", "https", "ftp", "mailto"]
ALLOWED_ATTRIBUTES = {
    "a": ["href", "title", "target", "rel"],
    "img": ["src", "alt", "title", "width", "height"],
}


def render_body(raw_body):
    """
    Render raw_body to HTML.

    This includes the following steps:

    * Convert Markdown to HTML
    * Sanitise HTML using bleach

    Note that this does not prevent Markdown syntax inside a MathJax block from
    being processed, which the forums JavaScript code does.
    """
    rendered_html = markdown.markdown(raw_body)
    sanitised_html = bleach.clean(
        rendered_html,
        tags=ALLOWED_TAGS,
        protocols=ALLOWED_PROTOCOLS,
        strip=True,
        attributes=ALLOWED_ATTRIBUTES
    )
    return sanitised_html
