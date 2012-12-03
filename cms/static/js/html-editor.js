var $body;
var $htmlEditor;
var $visualEditor;
var $assetWidget;
var $linkDialog;
var visualEditor;
var htmlEditor;
var htmlEditorTargetId;

function initHTMLEditor($editor, html, course_location) {
  $htmlEditor = $editor;
  htmlEditorTargetId = null;
  var _html = html;

  // there's a race condition here. wait a bit, then init tiny
  setTimeout(function() {
    $visualEditor = $editor.find('.edit-box.tinymce').tinymce({
      script_url : '/static/js/tiny_mce/tiny_mce.js',
      theme : "advanced",
      skin: 'studio',      
      
      // we may want to add "styleselect" when we collect all styles used throughout the lms
      theme_advanced_buttons1 : "formatselect,bold,italic,underline,studio.asset,bullist,numlist,outdent,indent,blockquote,link,unlink",
      theme_advanced_toolbar_location : "top",
      theme_advanced_toolbar_align : "left",
      theme_advanced_statusbar_location : "none",
      theme_advanced_resizing : true,
      theme_advanced_blockformats : "p,code,h2,h3,blockquote",
      content_css : "/static/css/html-editor.css",
      width: '100%',
      height: '400px',
      setup : function(ed) {
        ed.addButton('studio.asset', {
            title : 'Add Asset',
            image : '/static/img/visual-editor-image-icon.png',
            onclick : function() {
              $assetWidget = $($('#asset-library-widget').html());              
              $modalCover.unbind('click');
              $modalCover.bind('click', closeAssetWidget);
              $modalCover.css('z-index', '99999');
              // $('.upload-button', $assetWidget).bind('click', uploadFromWidget);
              //$('.close-button', $assetWidget).bind('click', closeAssetWidget);
              //$('.insert-asset-button', $assetWidget).bind('click', { editor: ed }, insertAsset);
              $body.append($assetWidget);
              $el = $body.find('.asset-library');

              $moduleEditor = new CMS.Views.AssetWidget({
                el: $el,
                model: new Backbone.Model({course_location: course_location}),
                editor: ed
              });
            }
        });
        ed.addButton('studio.link', {
            title : 'Add Link',
            image : '/static/img/visual-editor-image-icon.png',
            onclick : function() {
              $linkDialog = $($('#tiny-link-dialog').html());
              $modalCover.unbind('click');
              $modalCover.bind('click', closeLinkDialog);
              $modalCover.css('z-index', '99999');
              // $('.upload-button', $assetWidget).bind('click', uploadFromWidget);
              // $('.close-button', $assetWidget).bind('click', closeAssetWidget);
              // $('.insert-asset-button', $assetWidget).bind('click', { editor: ed }, insertAsset);
              $body.append($linkDialog);
            }
        });
      }
    });

    if(_html != null) {
      htmlEditor.setValue(_html)
      convertHTMLToVisual()
    }
  }, 100);
  
  htmlEditor = CodeMirror.fromTextArea($editor.find('.html-box')[0], {
    lineWrapping: true,
    mode: 'text/html',
    lineNumbers: true
  });

  $editor.find('.save-button').bind('click', saveHTMLEditor);
  $editor.find('.cancel-button').bind('click', cancelHTMLEditor);
}

function closeLinkDialog(e) {

}

function uploadFromWidget(e) {
  $('.library', $assetWidget).hide();
  $('.upload-form', $assetWidget).show();
  $('.choose-file-button', $assetWidget).bind('click', function(e) {
      e.preventDefault();
      $('.file-input', $assetWidget).click();
      $('.file-input', $assetWidget).bind('change', startUpload);
  });
}

function startUploadFromWidget(e) {
  $('.upload-modal h1').html('Uploading…');
  $('.upload-modal .file-name').html($('.file-input').val().replace('C:\\fakepath\\', ''));
  $('.upload-modal .file-chooser').ajaxSubmit({
      beforeSend: resetUploadBar,
      uploadProgress: showUploadFeedback,
      complete: displayFinishedUpload
  });
  $('.upload-modal .choose-file-button').hide();
  $('.upload-modal .progress-bar').removeClass('loaded').show();
}

function insertAsset(e) {
  closeAssetWidget();
  var editor = e.data.editor;
  editor.focus();
  editor.selection.setContent($(this).attr('data-markup'));
}

function closeAssetWidget(e) {
  $assetWidget.remove();
  $modalCover.css('z-index', '1000');
}

function convertVisualToHTML() {
  console.log('convert');
  htmlEditor.setValue($visualEditor.html());
}

function convertHTMLToVisual() {
  $visualEditor.html(htmlEditor.getValue());
}

function updateHTMLPreview() {
  //if(currentEditor == htmlEditor) {
  //  $htmlPreview.html(htmlEditor.getValue());
  //} else {
  //  $htmlPreview.html($visualEditor.html());
  //}
}

function getHTMLContent() {
  if(currentEditor == htmlEditor) {
    return htmlEditor.getValue();
  } else {
    return $visualEditor.html();
  }  
}

function saveHTMLEditor() {

}

function cancelHTMLEditor() {

}