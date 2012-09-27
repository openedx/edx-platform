class @SequenceDescriptor extends XModule.Descriptor
  constructor: (@element) ->
    @$tabs = $(@element).find("#sequence-list")
    @$tabs.sortable()
