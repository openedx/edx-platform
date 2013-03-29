class @XMLEditingDescriptor extends XModule.Descriptor
  constructor: (@element) ->
    @edit_box = CodeMirror.fromTextArea($(".edit-box", @element)[0], {
      mode: "xml"
      lineNumbers: true
      lineWrapping: true
    })

  save: ->
    data: @edit_box.getValue()
