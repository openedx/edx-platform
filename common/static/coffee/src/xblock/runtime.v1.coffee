@XBlock.runtime.v1 = (element, children) ->
  childMap = {}
  $.each children, (idx, child) ->
    childMap[child.name] = child

  return {
    handlerUrl: (handlerName) ->
      handlerPrefix = $(element).data("handler-prefix")
      "#{handlerPrefix}/#{handlerName}"
    children: children
    childMap: childMap
  }
