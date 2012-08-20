class @DiscussionUtil
  @getDiscussionData: (id) ->
    if id instanceof $
      id = id.attr("_id")
    else if typeof id == "object"
      id = $(id).attr("_id")
    return $$discussion_data[id]
