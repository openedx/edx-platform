var $body;
var $modal;
var $modalCover;
var $newComponentItem;
var $newComponentStep1;
var $newComponentStep2;

$(document).ready(function() {
  $body = $('body');
  $modal = $('.history-modal');
  $modalCover = $('.modal-cover');
  $newComponentItem = $('.new-component-item');
  $newComponentStep1 = $('.new-component-step-1');
  $newComponentStep2 = $('.new-component-step-2');
  $newComponentButton = $('.new-component-button');

  $('.expand-collapse-icon').bind('click', toggleSubmodules);
  $('.visibility-options').bind('change', setVisibility);

  $body.delegate('.xmodule_edit .edit-button', 'click', editComponent);
  $body.delegate('.component-editor .save-button, .component-editor .cancel-button', 'click', closeComponentEditor);

  $newComponentButton.bind('click', showNewComponentForm);
  $newComponentStep1.find('.new-component-type a').bind('click', showNewComponentProperties);
  $newComponentStep2.find('.save-button').bind('click', saveNewComponent);
  $newComponentStep2.find('.cancel-button').bind('click', cancelNewComponent);

  $('.unit-history ol a').bind('click', showHistoryModal);
  $modal.bind('click', hideHistoryModal);
  $modalCover.bind('click', hideHistoryModal);

    XModule.loadModules('display');
});

function toggleSubmodules(e) {
  e.preventDefault();
  $(this).toggleClass('expand').toggleClass('collapse');
  $(this).closest('.branch, .window').toggleClass('collapsed');
}

function setVisibility(e) {
  $(this).find('.checked').removeClass('checked');
  $(e.target).closest('.option').addClass('checked');
}

function editComponent(e) {
  e.preventDefault();
  $(this).closest('.xmodule_edit').addClass('editing').find('.component-editor').slideDown(150);
}

function closeComponentEditor(e) {
  e.preventDefault();
  $(this).closest('.xmodule_edit').removeClass('editing').find('.component-editor').slideUp(150);
}

function showNewComponentForm(e) {
  e.preventDefault();  
  $newComponentItem.addClass('adding');
  $(this).slideUp(150);
  $newComponentStep1.slideDown(150);
}

function showNewComponentProperties(e) {
  e.preventDefault();

  var displayName;
  var componentSource;
  var selectionRange;
  var $renderedComponent;

  switch($(this).attr('data-type')) {
    case 'video':
      displayName = 'Video';
      componentSource = '<video youtube="1.50:___,1.25:___,1.0:___,0.75:___"/>';
      selectionRange = [21, 24];
      $renderedComponent = $('<div class="rendered-component"><div class="video-unit"><img src="images/video-module.png"></div></div>');
      break;
    case 'textbook':
      displayName = 'Textbook';
      componentSource = '<customtag page="___"><impl>book</impl></customtag>';
      selectionRange = [17, 20];
      $renderedComponent = $('<div class="rendered-component"><p><span class="textbook-icon"></span>More information given in the text.</p></div>');
      break;
    case 'slide':
      displayName = 'Slide';
      componentSource = '<customtag page="___"><customtag lecnum="___"><impl>slides</impl></customtag>';
      selectionRange = [17, 20];
      $renderedComponent = $('<div class="rendered-component"><p><span class="slides-icon"></span>Lecture Slides Handout [Clean] [Annotated]</p></div>');
      break;
    case 'discussion':
      displayName = 'Discussion';
      componentSource = '<discussion for="___" id="___" discussion_category="___"/>';
      selectionRange = [17, 20];
      $renderedComponent = $('<div class="rendered-component"><div class="discussion-unit"><img src="images/discussion-module.png"></div></div>');
      break;
    case 'problem':
      displayName = 'Problem';
      componentSource = '<problem>___</problem>';
      selectionRange = [9, 12];
      $renderedComponent = $('<div class="rendered-component"></div>');
      break;
    case 'freeform':
      displayName = 'Freeform HTML';
      componentSource = '';
      selectionRange = [0, 0];
      $renderedComponent = $('<div class="rendered-component"></div>');
      break;
  }

  $newComponentItem.prepend($renderedComponent);
  $renderedComponent.slideDown(250);

  $newComponentStep2.find('h5').html('Edit ' + displayName + ' Component');
  $newComponentStep2.find('textarea').html(componentSource);
  setTimeout(function() {
    $newComponentStep2.find('textarea').focus().get(0).setSelectionRange(selectionRange[0], selectionRange[1]);  
  }, 10);  

  $newComponentStep1.slideUp(250);
  $newComponentStep2.slideDown(250);
}

function cancelNewComponent(e) {
  e.preventDefault();

  $newComponentStep2.slideUp(250);
  $newComponentButton.slideDown(250);
  $newComponentItem.removeClass('adding');
  $newComponentItem.find('.rendered-component').remove();
}

function saveNewComponent(e) {
  e.preventDefault();

  var $newComponent = $newComponentItem.clone();
  $newComponent.removeClass('adding').removeClass('new-component-item');
  $newComponent.find('.new-component-step-2').removeClass('new-component-step-2').addClass('component-editor');
  setTimeout(function() {
    $newComponent.find('.component-editor').slideUp(250);
  }, 10);  
  $newComponent.append('<div class="component-actions"><a href="#" class="edit-button"><span class="edit-icon white"></span>Edit</a><a href="#" class="delete-button"><span class="delete-icon white"></span>Delete</a>  </div><a href="#" class="drag-handle"></a>');
  $newComponent.find('.new-component-step-1').remove();
  $newComponent.find('.new-component-button').remove();

  $newComponentStep2.slideUp(250);
  $newComponentButton.slideDown(250);
  $newComponentItem.removeClass('adding');
  $newComponentItem.find('.rendered-component').remove();

  $newComponentItem.before($newComponent);
}

function showHistoryModal(e) {
  e.preventDefault();

  $modal.show();
  $modalCover.show();
}

function hideHistoryModal(e) {
  e.preventDefault();

  $modal.hide();
  $modalCover.hide();
}






