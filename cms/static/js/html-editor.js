var $body;
var $htmlPreview;
var $htmlEditor;
var htmlEditor;

function initHTMLEditor($editor, $prev) {
  /*
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
  */

  /*
  $htmlEditor = $editor;
  $htmlPreview = $prev;

  $('.edit-box', $editor).ckeditor();
  var $newEditor = $('.edit-box', $editor).ckeditorGet();
  console.log($newEditor);
  $newEditor.on('setData.ckeditor', function() {
    console.log('change');
  });
  */

  $htmlEditor = $editor;
  $htmlPreview = $prev;
  
  $editor.find('.edit-box.tinymce').tinymce({
    // Location of TinyMCE script
    script_url : '/static/js/tiny_mce/tiny_mce.js',

    // General options
    theme : "advanced",
    skin: 'studio',
    plugins : "autolink,lists,pagebreak,style,layer,table,save,advhr,advimage,advlink,emotions,iespell,inlinepopups,insertdatetime,preview,media,searchreplace,print,contextmenu,paste,directionality,fullscreen,noneditable,visualchars,nonbreaking,xhtmlxtras,template,advlist",

    // Theme options
    // we may want to add "styleselect" when we collect all styles used throught the lms
    theme_advanced_buttons1 : "bold,italic,underline,formatselect,bullist,numlist,outdent,indent,blockquote,link,unlink,code",
    theme_advanced_toolbar_location : "top",
    theme_advanced_toolbar_align : "left",
    theme_advanced_statusbar_location : "none",
    theme_advanced_resizing : true,
    theme_advanced_blockformats : "p,code,h2,h3,h4,h5,h6,blockquote",

    // Example content CSS (should be your site CSS)
    content_css : "/static/css/html-editor.css",
    width: '100%',
    height: '400px',
    setup : function(ed) {
      ed.onChange.add(onHTMLEditorUpdate);
      ed.onKeyUp.add(onHTMLEditorUpdate);
    }
  });

}

function onHTMLEditorUpdate(e) {
  // codemirror
  // $htmlPreview.html(htmlEditor.getValue());

  // tiny
  $htmlPreview.html($('.edit-box', htmlEditor).html());
}