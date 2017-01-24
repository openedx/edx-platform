class @JSONEditingDescriptor extends XModule.Descriptor
  constructor: (@element) ->
    @edit_box = CodeMirror.fromTextArea($(".edit-box", @element)[0], {
      mode: { name: "javascript", json: true }
      lineNumbers: true
      lineWrapping: true
    })

  save: ->
    data: JSON.parse @edit_box.getValue()
