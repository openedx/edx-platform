var $body;
var $htmlPreview;
var $htmlEditor;
var $visualEditor;
var $assetWidget;
var visualEditor;
var htmlEditor;

function initHTMLEditor($editor, $prev) {
  $htmlEditor = $editor;
  $htmlPreview = $prev;

  // there's a race condition here. wait a bit, then init tiny
  setTimeout(function() {
    $visualEditor = $editor.find('.edit-box.tinymce').tinymce({
      script_url : '/static/js/tiny_mce/tiny_mce.js',
      theme : "advanced",
      skin: 'studio',      
      
      // we may want to add "styleselect" when we collect all styles used throught the lms
      theme_advanced_buttons1 : "formatselect,bold,italic,underline,bullist,numlist,outdent,indent,blockquote,studio.asset,link,unlink",
      theme_advanced_toolbar_location : "top",
      theme_advanced_toolbar_align : "left",
      theme_advanced_statusbar_location : "none",
      theme_advanced_resizing : true,
      theme_advanced_blockformats : "p,code,h2,h3,h4,h5,h6,blockquote",
      content_css : "/static/css/html-editor.css",
      width: '100%',
      height: '400px',
      setup : function(ed) {
        ed.addButton('studio.asset', {
            title : 'Add Asset',
            image : '/static/img/visual-editor-image-icon.png',
            onclick : function() {
              $assetWidget = $($('#asset-library-widget').html());
              $('.insert-asset-button', $assetWidget).bind('click', { editor: ed }, insertAsset);
              $body.append($assetWidget);
            }
        });
      }
    });
  }, 100);

  htmlEditor = CodeMirror.fromTextArea($editor.find('.html-box')[0], {
    lineWrapping: true,
    mode: 'text/html',
    lineNumbers: true
  });

  $editor.find('.save-button, .cancel-button').bind('click', updatePreview);
}

function insertAsset(e) {
  $assetWidget.remove();
  var editor = e.data.editor;
  editor.focus();
  editor.selection.setContent($(this).attr('data-markup'));
}

function convertVisualToHTML() {
  htmlEditor.setValue($visualEditor.html());
}

function convertHTMLToVisual() {
  $visualEditor.html(htmlEditor.getValue());
}

function updatePreview() {
  $htmlPreview.html($visualEditor.html());
}

