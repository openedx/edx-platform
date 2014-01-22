@XBlock.runtime.v1 = (element, children) ->
  childMap = {}
  $.each children, (idx, child) ->
    childMap[child.name] = child

  return {
    # Generate the handler url for the specified handler.
    #
    # element is the html element containing the xblock requesting the url
    # handlerName is the name of the handler
    # suffix is the optional url suffix to include in the handler url
    # query is an optional query-string (note, this should not include a preceding ? or &)
    handlerUrl: (element, handlerName, suffix, query) ->
      handlerPrefix = $(element).data("handler-prefix")
      suffix = if suffix? then "/#{suffix}" else ''
      query = if query? then "?#{query}" else ''
      "#{handlerPrefix}/#{handlerName}#{suffix}#{query}"

    # A list of xblock children of this element
    children: children

    # A map of name -> child for the xblock children of this element
    childMap: childMap
  }
