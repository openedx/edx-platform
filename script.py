from opaque_keys.edx.keys import CourseKey

from xmodule.modulestore.django import modulestore
from xmodule.tabs import StaticTab


def create_new_list(requested_tab_id_locators, old_tab_list):
    """
    Helper function for creating a new course tab list in the new order
    of reordered tabs
    """
    new_tab_list = []
    for tab_id_locator in requested_tab_id_locators:
        tab = get_tab_by_tab_id_locator(old_tab_list, tab_id_locator)
        if tab is None:
            raise ValidationError({"error": f"Tab with id_locator '{tab_id_locator}' does not exist."})
        new_tab_list.append(tab)
    # the old_tab_list may contain additional tabs that were not rendered in the UI because of
    # global or course settings.  so add those to the end of the list.
    non_displayed_tabs = set(old_tab_list) - set(new_tab_list)
    new_tab_list.extend(non_displayed_tabs)

    # validate the tabs to make sure everything is Ok (e.g., did the client try to reorder unmovable tabs?)
    try:
        CourseTabList.validate_tabs(new_tab_list)
    except InvalidTabsException as exception:
        raise ValidationError({"error": f"New list of tabs is not valid: {str(exception)}."}) from exception

    # persist the new order of the tabs
    # course_item.tabs = new_tab_list
    # modulestore().update_item(course_item, user.id)
    return new_tab_list


course_module = modulestore().get_course(CourseKey.from_string("course-v1:ArbiX+CS101+2021_T4"))

print(course_module)

breakpoint()

tab_idx = 0
old_tab_dict = {}
for tab in course_module.tabs:
    if isinstance(tab, StaticTab) or tab.type == "courseware":
        old_tab_dict[tab] = tab_idx
    tab_idx += 1
old_tab_list = list(old_tab_dict.keys())

new_tab_list = create_new_list([], old_tab_list)

full_new_tab_list = course_module.tabs
original_idx = list(old_tab_dict.values())
for i in range(len(new_tab_list)):
    full_new_tab_list[original_idx[i]] = new_tab_list[i]



all_course_tabs = course_item.tabs
course_static_tabs = {
    tab_index: tab
    for tab, tab_index in enumerate(all_course_tabs)
    if isinstance(tab, StaticTab)
}
current_course_tabs = list(static_tabs.values())
current_course_tab_ids = list(static_tabs.keys())

new_course_tabs = create_new_list(requested_tab_id_locators, current_course_tabs)





