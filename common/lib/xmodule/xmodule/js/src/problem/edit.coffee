class @MarkdownEditingDescriptor extends XModule.Descriptor
  constructor: (element) ->
#    $body.on('click', '.editor-tabs .tab', @changeEditor)
    $('.editor-tabs .tab').bind 'click', (event) => @changeEditor(event)
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

  changeEditor: (e) ->
    e.preventDefault();
    $('.editor-tabs .current').removeClass('current')
    $(this).addClass('current');
    if (@current_editor == @xml_editor)
      @setCurrentEditor(@markdown_editor)
    else
      @setCurrentEditor(@xml_editor)


#    switch($(this).attr('data-tab')) {
#    case 'simple':
#    currentEditor = simpleEditor;
#    $(simpleEditor.getWrapperElement()).show();
#    $(xmlEditor.getWrapperElement()).hide();
#    $(simpleEditor).focus();
#    onSimpleEditorUpdate();
#    break;
#    case 'xml':
#    currentEditor = xmlEditor;
#    $(simpleEditor.getWrapperElement()).hide();
#    $(xmlEditor.getWrapperElement()).show();
#    $(xmlEditor).focus();
#    xmlEditor.refresh();
#    break;

  setCurrentEditor: (editor) ->
    $(@current_editor.getWrapperElement()).hide()
    @current_editor = editor
    $(@current_editor.getWrapperElement()).show()
    $(@current_editor).focus();

  save: ->
#    TODO: make sure this gets unregistered correctly (changed how registration works)
    $body.off('click', '.editor-tabs .tab', @changeEditor)
    data: @xml_editor.getValue()
