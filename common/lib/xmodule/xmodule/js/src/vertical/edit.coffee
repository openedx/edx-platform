class @VerticalDescriptor extends XModule.Descriptor
  constructor: (@element) ->
    @$items = $(@element).find(".vert-mod")
    @$items.sortable()
