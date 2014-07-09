import re
import logging

from xmodule.contentstore.content import StaticContent


def _prefix_only_url_replace_regex(prefix):
    """
    Match static urls in quotes that don't end in '?raw'.

    To anyone contemplating making this more complicated:
    http://xkcd.com/1171/
    """
    return ur"""
        (?x)                      # flags=re.VERBOSE
        (?P<quote>\\?['"])        # the opening quotes
        (?P<prefix>{prefix})      # the prefix
        (?P<rest>.*?)             # everything else in the url
        (?P=quote)                # the first matching closing quote
        """.format(prefix=re.escape(prefix))


def _prefix_and_category_url_replace_regex(prefix):
    """
    Match static urls in quotes that don't end in '?raw'.

    To anyone contemplating making this more complicated:
    http://xkcd.com/1171/
    """
    return ur"""
        (?x)                      # flags=re.VERBOSE
        (?P<quote>\\?['"])        # the opening quotes
        (?P<prefix>{prefix})      # the prefix
        (?P<category>[^/]+)/
        (?P<rest>.*?)             # everything else in the url
        (?P=quote)                # the first matching closing quote
        """.format(prefix=re.escape(prefix))


def rewrite_nonportable_content_links(source_course_id, dest_course_id, text):
    """
    Does a regex replace on non-portable links:
         /c4x/<org>/<course>/asset/<name> -> /static/<name>
         /jump_to/i4x://<org>/<course>/<category>/<name> -> /jump_to_id/<id>

    """

    def portable_asset_link_subtitution(match):
        quote = match.group('quote')
        rest = match.group('rest')
        return quote + '/static/' + rest + quote

    def portable_jump_to_link_substitution(match):
        quote = match.group('quote')
        rest = match.group('rest')
        return quote + '/jump_to_id/' + rest + quote

    # NOTE: ultimately link updating is not a hard requirement, so if something blows up with
    # the regex substitution, log the error and continue
    c4x_link_base = StaticContent.get_base_url_path_for_course_assets(source_course_id)
    try:
        text = re.sub(_prefix_only_url_replace_regex(c4x_link_base), portable_asset_link_subtitution, text)
    except Exception as exc:  # pylint: disable=broad-except
        logging.warning("Error producing regex substitution %r for text = %r.\n\nError msg = %s", c4x_link_base, text, str(exc))

    jump_to_link_base = u'/courses/{course_key_string}/jump_to/i4x://{course_key.org}/{course_key.course}/'.format(
        course_key_string=source_course_id.to_deprecated_string(), course_key=source_course_id
    )
    try:
        text = re.sub(_prefix_and_category_url_replace_regex(jump_to_link_base), portable_jump_to_link_substitution, text)
    except Exception as exc:  # pylint: disable=broad-except
        logging.warning("Error producing regex substitution %r for text = %r.\n\nError msg = %s", jump_to_link_base, text, str(exc))

    # Also, there commonly is a set of link URL's used in the format:
    # /courses/<org>/<course>/<name> which will be broken if migrated to a different course_id
    # so let's rewrite those, but the target will also be non-portable,
    #
    # Note: we only need to do this if we are changing course-id's
    #
    if source_course_id != dest_course_id:
        try:
            generic_courseware_link_base = u'/courses/{}/'.format(source_course_id.to_deprecated_string())
            text = re.sub(_prefix_only_url_replace_regex(generic_courseware_link_base), portable_asset_link_subtitution, text)
        except Exception as exc:  # pylint: disable=broad-except
            logging.warning("Error producing regex substitution %r for text = %r.\n\nError msg = %s", source_course_id, text, str(exc))

    return text
