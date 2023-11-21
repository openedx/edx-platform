from typing import Callable


def handle_children_duplication(
    xblock, source_item, store, user, duplication_function: Callable[..., None], shallow: bool
):
    if not source_item.has_children or shallow:
        return

    xblock.children = xblock.children or []
    for child in source_item.children:
        dupe = duplication_function(xblock.location, child, user=user, is_child=True)
        if dupe not in xblock.children:  # duplicate_fun may add the child for us.
            xblock.children.append(dupe)
    store.update_item(xblock, user.id)
