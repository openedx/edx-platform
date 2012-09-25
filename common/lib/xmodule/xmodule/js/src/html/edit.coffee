class @HTMLEditingDescriptor
  constructor: (@element) ->
    @edit_box = CodeMirror.fromTextArea($(".edit-box", @element)[0], {
      mode: "text/html"
    })

  save: -> @edit_box.getValue()
