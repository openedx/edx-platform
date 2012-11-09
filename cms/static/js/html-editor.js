var $body;
var $htmlPreview;
var $htmlEditor;
var htmlEditor;

function initHTMLEditor($editor, $prev) {
  $htmlEditor = $editor;
  htmlEditor = CodeMirror.fromTextArea($editor.find('.edit-box')[0], {
    lineWrapping: true,
    mode: 'xml',
    lineNumbers: true,
    onChange: onHTMLEditorUpdate
  });

  currentEditor = htmlEditor;

  $(htmlEditor.getWrapperElement()).css({
    'background': '#fff'
  });
  $(htmlEditor.getWrapperElement()).bind('click', function() {
    $(htmlEditor).focus();
  });
  $(htmlEditor).focus();
  $htmlPreview = $prev;
}

function onHTMLEditorUpdate(e) {
  $htmlPreview.html(htmlEditor.getValue());
}