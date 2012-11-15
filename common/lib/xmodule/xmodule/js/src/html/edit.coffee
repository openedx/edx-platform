class @HTMLEditingDescriptor
  constructor: (@element) ->
    @edit_box = CodeMirror.fromTextArea($(".edit-box", @element)[0], {
      lineNumbers: true
      lineWrapping: true
    })

  save: ->
    data: @edit_box.getValue()

