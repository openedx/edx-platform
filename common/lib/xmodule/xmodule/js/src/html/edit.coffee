class @HTMLEditingDescriptor
  constructor: (@element) ->
    text = $(".edit-box", @element)[0];
    replace_func = (elt) -> text.parentNode.replaceChild(elt, text)
    @edit_box = CodeMirror(replace_func, {
      value: text.innerHTML
      mode: "text/html"
      lineNumbers: true
      lineWrapping: true})

  save: ->
    data: @edit_box.getValue()
