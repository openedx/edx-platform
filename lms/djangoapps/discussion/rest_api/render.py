"""
Content rendering functionality

Note that this module is designed to imitate the front end behavior as
implemented in Markdown.Sanitizer.js.
"""


import re

import markdown

# These patterns could be more flexible about things like attributes and
# whitespace, but this is imitating Markdown.Sanitizer.js, so it uses the
# patterns defined therein.
TAG_PATTERN = re.compile(r"<[^>]*>?")
SANITIZED_TAG_PATTERN = re.compile(r"<(/?)(\w+)[^>]*>")
ALLOWED_BASIC_TAG_PATTERN = re.compile(
    r"^(</?(b|blockquote|code|del|dd|dl|dt|em|h1|h2|h3|i|kbd|li|ol|p|pre|s|sup|sub|strong|strike|ul)>|<(br|hr)\s?/?>)$"
)
ALLOWED_A_PATTERN = re.compile(
    r'^(<a\shref="((https?|ftp)://|/)[-A-Za-z0-9+&@#/%?=~_|!:,.;\(\)]+"(\stitle="[^"<>]+")?\s?>|</a>)$'
)
ALLOWED_IMG_PATTERN = re.compile(
    r'^(<img\ssrc="(https?://|/)[-A-Za-z0-9+&@#/%?=~_|!:,.;\(\)]+"(\swidth="\d{1,3}")?'
    r'(\sheight="\d{1,3}")?(\salt="[^"<>]*")?(\stitle="[^"<>]*")?\s?/?>)$'
)


def _sanitize_tag(match):
    """Return the tag if it is allowed or the empty string otherwise"""
    tag = match.group(0)
    if (
            ALLOWED_BASIC_TAG_PATTERN.match(tag) or
            ALLOWED_A_PATTERN.match(tag) or
            ALLOWED_IMG_PATTERN.match(tag)
    ):
        return tag
    else:
        return ""


def _sanitize_html(source):
    """
    Return source with all non-allowed tags removed, preserving the text content
    """
    return TAG_PATTERN.sub(_sanitize_tag, source)


def _remove_unpaired_tags(source):
    """
    Return source with all unpaired tags removed, preserving the text content

    source should have already been sanitized
    """
    tag_matches = list(SANITIZED_TAG_PATTERN.finditer(source))
    if not tag_matches:
        return source
    tag_stack = []
    tag_name_stack = []
    text_stack = [source[:tag_matches[0].start()]]
    for i, match in enumerate(tag_matches):
        tag_name = match.group(2)
        following_text = (
            source[match.end():tag_matches[i + 1].start()] if i + 1 < len(tag_matches) else
            source[match.end():]
        )
        if tag_name in ["p", "img", "br", "li", "hr"]:  # tags that don't require closing
            text_stack[-1] += match.group(0) + following_text
        elif match.group(1):  # end tag
            if tag_name in tag_name_stack:  # paired with a start tag somewhere
                # pop tags until we find the matching one, keeping the non-tag text
                while True:
                    popped_tag_name = tag_name_stack.pop()
                    popped_tag = tag_stack.pop()
                    popped_text = text_stack.pop()
                    if popped_tag_name == tag_name:
                        text_stack[-1] += popped_tag + popped_text + match.group(0)
                        break
                    else:
                        text_stack[-1] += popped_text
            # else unpaired; drop the tag
            text_stack[-1] += following_text
        else:  # start tag
            tag_stack.append(match.group(0))
            tag_name_stack.append(tag_name)
            text_stack.append(following_text)
    return "".join(text_stack)


def render_body(raw_body):
    """
    Render raw_body to HTML.

    This includes the following steps:

    * Convert Markdown to HTML
    * Strip non-whitelisted HTML
    * Remove unbalanced HTML tags

    Note that this does not prevent Markdown syntax inside a MathJax block from
    being processed, which the forums JavaScript code does.
    """
    rendered = markdown.markdown(raw_body)
    rendered = _sanitize_html(rendered)
    rendered = _remove_unpaired_tags(rendered)
    return rendered
