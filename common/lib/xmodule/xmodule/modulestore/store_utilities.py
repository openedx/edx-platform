import re
from xmodule.contentstore.content import StaticContent
from xmodule.modulestore import Location

import logging


def _prefix_only_url_replace_regex(prefix):
    """
    Match static urls in quotes that don't end in '?raw'.

    To anyone contemplating making this more complicated:
    http://xkcd.com/1171/
    """
    return r"""
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
    return r"""
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

    org, course, run = source_course_id.split("/")
    dest_org, dest_course, dest_run = dest_course_id.split("/")

    def portable_asset_link_subtitution(match):
        quote = match.group('quote')
        rest = match.group('rest')
        return quote + '/static/' + rest + quote

    def portable_jump_to_link_substitution(match):
        quote = match.group('quote')
        rest = match.group('rest')
        return quote + '/jump_to_id/' + rest + quote

    def generic_courseware_link_substitution(match):
        quote = match.group('quote')
        rest = match.group('rest')
        dest_generic_courseware_lik_base = '/courses/{org}/{course}/{run}/'.format(
            org=dest_org, course=dest_course, run=dest_run
        )
        return quote + dest_generic_courseware_lik_base + rest + quote

    course_location = Location(['i4x', org, course, 'course', run])

    # NOTE: ultimately link updating is not a hard requirement, so if something blows up with
    # the regex subsitution, log the error and continue
    try:
        c4x_link_base = u'{0}/'.format(StaticContent.get_base_url_path_for_course_assets(course_location))
        text = re.sub(_prefix_only_url_replace_regex(c4x_link_base), portable_asset_link_subtitution, text)
    except Exception, e:
        logging.warning("Error going regex subtituion %r on text = %r.\n\nError msg = %s", c4x_link_base, text, str(e))

    try:
        jump_to_link_base = u'/courses/{org}/{course}/{run}/jump_to/i4x://{org}/{course}/'.format(
            org=org, course=course, run=run
        )
        text = re.sub(_prefix_and_category_url_replace_regex(jump_to_link_base), portable_jump_to_link_substitution, text)
    except Exception, e:
        logging.warning("Error going regex subtituion %r on text = %r.\n\nError msg = %s", jump_to_link_base, text, str(e))

    # Also, there commonly is a set of link URL's used in the format:
    # /courses/<org>/<course>/<run> which will be broken if migrated to a different course_id
    # so let's rewrite those, but the target will also be non-portable,
    #
    # Note: we only need to do this if we are changing course-id's
    #
    if source_course_id != dest_course_id:
        try:
            generic_courseware_link_base = u'/courses/{org}/{course}/{run}/'.format(
                org=org, course=course, run=run
            )
            text = re.sub(_prefix_only_url_replace_regex(generic_courseware_link_base), portable_asset_link_subtitution, text)
        except Exception, e:
            logging.warning("Error going regex subtituion %r on text = %r.\n\nError msg = %s", generic_courseware_link_base, text, str(e))

    return text


def _clone_modules(modulestore, modules, source_location, dest_location):
    for module in modules:
        original_loc = Location(module.location)

        if original_loc.category != 'course':
            module.location = module.location._replace(
                tag=dest_location.tag,
                org=dest_location.org,
                course=dest_location.course
            )
        else:
            # on the course module we also have to update the module name
            module.location = module.location._replace(
                tag=dest_location.tag,
                org=dest_location.org,
                course=dest_location.course,
                name=dest_location.name
            )

        print "Cloning module {0} to {1}....".format(original_loc, module.location)

        if 'data' in module.fields and module.fields['data'].is_set_on(module) and isinstance(module.data, basestring):
            module.data = rewrite_nonportable_content_links(
                source_location.course_id, dest_location.course_id, module.data)

        # repoint children
        if module.has_children:
            new_children = []
            for child_loc_url in module.children:
                child_loc = Location(child_loc_url)
                child_loc = child_loc._replace(
                    tag=dest_location.tag,
                    org=dest_location.org,
                    course=dest_location.course
                )
                new_children.append(child_loc.url())

            module.children = new_children

        modulestore.update_item(module, '_clone_modules')


def clone_course(modulestore, contentstore, source_location, dest_location, delete_original=False):
    # check to see if the dest_location exists as an empty course
    # we need an empty course because the app layers manage the permissions and users
    if not modulestore.has_item(dest_location.course_id, dest_location):
        raise Exception("An empty course at {0} must have already been created. Aborting...".format(dest_location))

    # verify that the dest_location really is an empty course, which means only one with an optional 'overview'
    dest_modules = modulestore.get_items([dest_location.tag, dest_location.org, dest_location.course, None, None, None])

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
    if not modulestore.has_item(source_location.course_id, source_location):
        raise Exception("Cannot find a course at {0}. Aborting".format(source_location))

    # Get all modules under this namespace which is (tag, org, course) tuple

    modules = modulestore.get_items([source_location.tag, source_location.org, source_location.course, None, None, None])
    _clone_modules(modulestore, modules, source_location, dest_location)

    modules = modulestore.get_items([source_location.tag, source_location.org, source_location.course, None, None, 'draft'])
    _clone_modules(modulestore, modules, source_location, dest_location)

    # now iterate through all of the assets and clone them
    # first the thumbnails
    thumbs = contentstore.get_all_content_thumbnails_for_course(source_location)
    for thumb in thumbs:
        thumb_loc = Location(thumb["_id"])
        content = contentstore.find(thumb_loc)
        content.location = content.location._replace(org=dest_location.org,
                                                     course=dest_location.course)

        print "Cloning thumbnail {0} to {1}".format(thumb_loc, content.location)

        contentstore.save(content)

    # now iterate through all of the assets, also updating the thumbnail pointer

    assets, __ = contentstore.get_all_content_for_course(source_location)
    for asset in assets:
        asset_loc = Location(asset["_id"])
        content = contentstore.find(asset_loc)
        content.location = content.location._replace(org=dest_location.org,
                                                     course=dest_location.course)

        # be sure to update the pointer to the thumbnail
        if content.thumbnail_location is not None:
            content.thumbnail_location = content.thumbnail_location._replace(org=dest_location.org,
                                                                             course=dest_location.course)

        print "Cloning asset {0} to {1}".format(asset_loc, content.location)

        contentstore.save(content)

    return True


def _delete_modules_except_course(modulestore, modules, source_location, commit):
    """
    This helper method will just enumerate through a list of modules and delete them, except for the
    top-level course module
    """
    for module in modules:
        if module.category != 'course':
            logging.warning("Deleting {0}...".format(module.location))
            if commit:
                # sanity check. Make sure we're not deleting a module in the incorrect course
                if module.location.org != source_location.org or module.location.course != source_location.course:
                    raise Exception('Module {0} is not in same namespace as {1}. This should not happen! Aborting...'.format(module.location, source_location))
                modulestore.delete_item(module.location)


def _delete_assets(contentstore, assets, commit):
    """
    This helper method will enumerate through a list of assets and delete them
    """
    for asset in assets:
        asset_loc = Location(asset["_id"])
        id = StaticContent.get_id_from_location(asset_loc)
        logging.warning("Deleting {0}...".format(id))
        if commit:
            contentstore.delete(id)


def delete_course(modulestore, contentstore, source_location, commit=False):
    """
    This method will actually do the work to delete all content in a course in a MongoDB backed
    courseware store. BE VERY CAREFUL, this is not reversable.
    """

    # check to see if the source course is actually there
    if not modulestore.has_item(source_location.course_id, source_location):
        raise Exception("Cannot find a course at {0}. Aborting".format(source_location))

    # first delete all of the thumbnails
    thumbs = contentstore.get_all_content_thumbnails_for_course(source_location)
    _delete_assets(contentstore, thumbs, commit)

    # then delete all of the assets
    assets, __ = contentstore.get_all_content_for_course(source_location)
    _delete_assets(contentstore, assets, commit)

    # then delete all course modules
    modules = modulestore.get_items([source_location.tag, source_location.org, source_location.course, None, None, None])
    _delete_modules_except_course(modulestore, modules, source_location, commit)

    # then delete all draft course modules
    modules = modulestore.get_items([source_location.tag, source_location.org, source_location.course, None, None, 'draft'])
    _delete_modules_except_course(modulestore, modules, source_location, commit)

    # finally delete the top-level course module itself
    print "Deleting {0}...".format(source_location)
    if commit:
        modulestore.delete_item(source_location)

    return True
