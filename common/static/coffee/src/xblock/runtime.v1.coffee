@XBlock.runtime.v1 = (element, children) ->
  childMap = {}
  $.each children, (idx, child) ->
    childMap[child.name] = child

  return {
    handlerUrl: (handlerName) ->
      usageId = $(element).data("usage-id")
      "/xblock/handler/#{usageId}/#{handlerName}"
    children: children
    childMap: childMap
  }
