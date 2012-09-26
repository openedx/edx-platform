class @VerticalDescriptor
  constructor: (@element) ->
    @$items = $(@element).find(".vert-mod")
    @$items.sortable()
