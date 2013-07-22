from xmodule.contentstore.content import StaticContent
from xmodule.modulestore import Location
from xmodule.modulestore.mongo import MongoModuleStore

import logging


def clone_course(modulestore, contentstore, source_location, dest_location, delete_original=False):
    # first check to see if the modulestore is Mongo backed
    if not isinstance(modulestore, MongoModuleStore):
        raise Exception("Expected a MongoModuleStore in the runtime. Aborting....")

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

    for module in modules:
        original_loc = Location(module.location)

        if original_loc.category != 'course':
            module.location = module.location._replace(tag=dest_location.tag, org=dest_location.org,
                                                       course=dest_location.course)
        else:
            # on the course module we also have to update the module name
            module.location = module.location._replace(tag=dest_location.tag, org=dest_location.org,
                                                       course=dest_location.course, name=dest_location.name)

        print "Cloning module {0} to {1}....".format(original_loc, module.location)

        modulestore.update_item(module.location, module._model_data._kvs._data)

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

            modulestore.update_children(module.location, new_children)

        # save metadata
        modulestore.update_metadata(module.location, module._model_data._kvs._metadata)

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

    assets = contentstore.get_all_content_for_course(source_location)
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
    assets = contentstore.get_all_content_for_course(source_location)
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
