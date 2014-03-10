import re
from xmodule.contentstore.content import StaticContent

import logging


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

    def generic_courseware_link_substitution(match):
        return u'{quote}/courses/{course_id}/{rest}{quote}'.format(
            quote=match.group('quote'),
            course_id=dest_course_id,
            rest=match.group('rest')
        )

    # NOTE: ultimately link updating is not a hard requirement, so if something blows up with
    # the regex subsitution, log the error and continue
    c4x_link_base = StaticContent.get_base_url_path_for_course_assets(source_course_id)
    try:
        text = re.sub(_prefix_only_url_replace_regex(c4x_link_base), portable_asset_link_subtitution, text)
    except Exception as e:
        logging.warning("Error going regex subtituion %r on text = %r.\n\nError msg = %s", c4x_link_base, text, str(e))

    jump_to_link_base = u'/courses/{course_key:s}/jump_to/i4x://{course_key.org}/{course_key.course}/'.format(
        course_key=source_course_id
    )
    try:
        text = re.sub(_prefix_and_category_url_replace_regex(jump_to_link_base), portable_jump_to_link_substitution, text)
    except Exception as e:
        logging.warning("Error on regex substituion %r for text = %r.\n\nError msg = %s", jump_to_link_base, text, str(e))

    # Also, there commonly is a set of link URL's used in the format:
    # /courses/<org>/<course>/<name> which will be broken if migrated to a different course_id
    # so let's rewrite those, but the target will also be non-portable,
    #
    # Note: we only need to do this if we are changing course-id's
    #
    if source_course_id != dest_course_id:
        try:
            generic_courseware_link_base = u'/courses/{org}/{course}/{name}/'.format(**course_id_dict)
            text = re.sub(_prefix_only_url_replace_regex(generic_courseware_link_base), portable_asset_link_subtitution, text)
        except Exception as e:
            logging.warning("Error going regex subtituion %r on text = %r.\n\nError msg = %s", generic_courseware_link_base, text, str(e))

    return text


def _clone_modules(modulestore, modules, source_course_id, dest_course_id):
    for module in modules:
        original_loc = module.location
        module.location = module.location.map_into_course(dest_course_id)

        print "Cloning module {0} to {1}....".format(original_loc, module.location)

        if 'data' in module.fields and module.fields['data'].is_set_on(module) and isinstance(module.data, basestring):
            module.data = rewrite_nonportable_content_links(
                source_course_id, dest_course_id, module.data
            )

        # repoint children
        if module.has_children:
            new_children = []
            for child_loc_url in module.children:
                child_loc = original_loc.course_key.make_usage_key_from_deprecated_string(child_loc_url)
                child_loc = child_loc.map_into_course(dest_course_id)
                new_children.append(child_loc.url())

            module.children = new_children

        modulestore.update_item(module, '**replace_user**')


def clone_course(modulestore, contentstore, source_course_id, dest_course_id, delete_original=False):
    # check to see if the dest_location exists as an empty course
    # we need an empty course because the app layers manage the permissions and users
    if not modulestore.has_course(dest_course_id):
        raise Exception("An empty course at {0} must have already been created. Aborting...".format(dest_course_id))

    # verify that the dest_location really is an empty course, which means only one with an optional 'overview'
    dest_modules = modulestore.get_items(CourseKey.from_string(dest_course_id))

    basically_empty = True
    for module in dest_modules:
        if module.location.category == 'course' or (module.location.category == 'about'
                                                    and module.location.name == 'overview'):
            continue

        basically_empty = False
        break

    if not basically_empty:
        raise Exception("Course at destination {0} is not an empty course. You can only clone into an empty course. Aborting...".format(dest_location))

    # check to see if the source course is actually there
    if not modulestore.has_course(source_course_id):
        raise Exception("Cannot find a course at {0}. Aborting".format(source_course_id))

    # Get all modules under this namespace which is (tag, org, course) tuple

    modules = modulestore.get_items(CourseKey.from_string(source_course_id), revision=None)
    _clone_modules(modulestore, modules, source_course_id, dest_course_id)

    modules = modulestore.get_items(CourseKey.from_string(source_course_id), revision='draft')
    _clone_modules(modulestore, modules, source_course_id, dest_course_id)

    # now iterate through all of the assets and clone them
    # first the thumbnails
    thumb_keys = contentstore.get_all_content_thumbnails_for_course(source_course_id)
    for thumb_key in thumb_keys:
        content = contentstore.find(thumb_key)
        content.location = content.location.map_into_course(dest_course_id)

        print "Cloning thumbnail {0} to {1}".format(thumb_key, content.location)

        contentstore.save(content)

    # now iterate through all of the assets, also updating the thumbnail pointer

    asset_keys, __ = contentstore.get_all_content_for_course(source_course_id)
    for asset_key in asset_keys:
        content = contentstore.find(asset_key)
        content.location = content.location.map_into_course(dest_course_id)

        # be sure to update the pointer to the thumbnail
        if content.thumbnail_location is not None:
            content.thumbnail_location = content.thumbnail_location.map_into_course(dest_course_id)

        print "Cloning asset {0} to {1}".format(asset_key, content.location)

        contentstore.save(content)

    return True


def delete_course(modulestore, contentstore, course_key, commit=False):
    """
    This method will actually do the work to delete all content in a course in a MongoDB backed
    courseware store. BE VERY CAREFUL, this is not reversable.
    """

    # check to see if the source course is actually there
    if not modulestore.has_course(course_key):
        raise Exception("Cannot find a course at {0}. Aborting".format(course_key))

    if commit:
        print "Deleting assets and thumbnails {}".format(course_key)
        contentstore.delete_all_course_assets(course_key)

    # finally delete the course
    print "Deleting {0}...".format(course_key)
    if commit:
        modulestore.delete_course(course_key, '**replace-user**')

        # remove location of this course from loc_mapper and cache
        loc_mapper().delete_course_mapping(course_key)

    return True
