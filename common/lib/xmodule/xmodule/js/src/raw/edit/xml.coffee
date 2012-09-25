class @XMLEditingDescriptor
  constructor: (@element) ->
    @edit_box = CodeMirror.fromTextArea($(".edit-box", @element)[0], {
      mode: "xml"
    })

  save: -> @edit_box.getValue()
