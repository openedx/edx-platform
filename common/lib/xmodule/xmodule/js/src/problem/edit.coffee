class @MarkdownEditingDescriptor extends XModule.Descriptor
  constructor: (element) ->
    $body.on('click', '.editor-tabs .tab', @changeEditor)

    @xml_editor = CodeMirror.fromTextArea($(".xml-box", element)[0], {
    mode: "xml"
    lineNumbers: true
    lineWrapping: true
    })
    @current_editor = @xml_editor

    if $(".markdown-box", element).length != 0
      @markdown_editor = CodeMirror.fromTextArea($(".markdown-box", element)[0], {
      lineWrapping: true
      mode: null
      onChange: @onMarkdownEditorUpdate
      })
      @setCurrentEditor(@markdown_editor)

  onMarkdownEditorUpdate:  ->
    console.log('update')
    @updateXML()

  updateXML: ->

  changeEditor: (e) =>
    e.preventDefault();
    $('.editor-tabs .current').removeClass('current')
    $(e.currentTarget).addClass('current')
    if (@current_editor == @xml_editor)
      @setCurrentEditor(@markdown_editor)
      #    onMarkdownEditorUpdate();
    else
      @setCurrentEditor(@xml_editor)
      #    xmlEditor.refresh();

  setCurrentEditor: (editor) ->
    $(@current_editor.getWrapperElement()).hide()
    @current_editor = editor
    $(@current_editor.getWrapperElement()).show()
    $(@current_editor).focus();

  save: ->
    $body.off('click', '.editor-tabs .tab', @changeEditor)
    data: @xml_editor.getValue()
