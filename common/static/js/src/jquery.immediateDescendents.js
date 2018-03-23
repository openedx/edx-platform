# Find all the children of an element that match the selector, but only
# the first instance found down any path.  For example, we'll find all
# the ".xblock" elements below us, but not the ones that are themselves
# contained somewhere inside ".xblock" elements.
jQuery.fn.immediateDescendents = (selector) ->
  @children().map ->
    elem = jQuery(this)
    if elem.is(selector)
      this
    else
      elem.immediateDescendents(selector).get()
