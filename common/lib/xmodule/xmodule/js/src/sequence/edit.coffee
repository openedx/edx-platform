class @SequenceDescriptor extends XModule.Descriptor
  constructor: (@element) ->
    @$tabs = $(@element).find("#sequence-list")
    @$tabs.sortable(
      update: (event, ui) => @update()
    )

  save: ->
    children: $('#sequence-list li a', @element).map((idx, el) -> $(el).data('id')).toArray()
