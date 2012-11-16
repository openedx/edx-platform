var $body;
var $htmlPreview;
var $htmlEditor;
var $visualEditor;
var visualEditor;
var htmlEditor;

function initHTMLEditor($editor, $prev) {
  $htmlEditor = $editor;
  $htmlPreview = $prev;

  // there's a race condition here. wait a bit, then init tiny
  setTimeout(function() {
    $editor.find('.edit-box.tinymce').tinymce({
      script_url : '/static/js/tiny_mce/tiny_mce.js',
      theme : "advanced",
      skin: 'studio',
      plugins : "autolink,pagebreak,style,layer,table,save,advhr,advimage,advlink,emotions,iespell,inlinepopups,insertdatetime,preview,media,searchreplace,print,contextmenu,paste,directionality,fullscreen,noneditable,visualchars,nonbreaking,xhtmlxtras,template",
      
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
              ed.focus();
              ed.selection.setContent('This should open the studio asset picker.');
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

function convertVisualToHTML() {
  htmlEditor.setValue($('.edit-box', visualEditor).html());
}

function convertHTMLToVisual() {
  $('.edit-box', visualEditor).html(htmlEditor.getValue());
}

function updatePreview() {
  $htmlPreview.html($('.edit-box', visualEditor).html());
}