class XBlock.Runtime.v1
  constructor: (@element, @children) ->
    @childMap = {}
    $.each @children, (idx, child) =>
      @childMap[child.name] = child
