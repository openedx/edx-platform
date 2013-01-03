class @MarkdownEditingDescriptor extends XModule.Descriptor
  constructor: (@element) ->
    @edit_box = CodeMirror.fromTextArea($(".xml-box", @element)[0], {
      mode: "xml"
      lineNumbers: true
      lineWrapping: true
    })

  save: ->
    data: @edit_box.getValue()
