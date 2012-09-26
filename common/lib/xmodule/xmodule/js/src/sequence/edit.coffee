class @SequenceDescriptor
  constructor: (@element) ->
    @$tabs = $(@element).find("#sequence-list")
    @$tabs.sortable()
