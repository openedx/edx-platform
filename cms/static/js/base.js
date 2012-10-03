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
    $newComponentTypePicker = $('.new-component');
    $newComponentTemplatePickers = $('.new-component-templates');
    $newComponentButton = $('.new-component-button');
    $body.bind('keyup', onKeyUp);

    $('.expand-collapse-icon').bind('click', toggleSubmodules);
    $('.visibility-options').bind('change', setVisibility);

    $('.unit-history ol a').bind('click', showHistoryModal);
    $modal.bind('click', hideModal);
    $modalCover.bind('click', hideHistoryModal);
    $('.assets .upload-button').bind('click', showUploadModal);
    $('.upload-modal .close-button').bind('click', hideModal);
    $('.unit .item-actions .delete-button').bind('click', deleteUnit);
});

function deleteUnit(e) {
    e.preventDefault();
    var id = $(this).data('id');
    var _this = $(this);
    
    $.post('/delete_item', 
	   {'id': id, 'delete_children' : 'true'}, 
	   function(data) {
	       // remove 'leaf' class containing <li> element
	       var parent = _this.parents('li.leaf');
	       parent.remove();
	   });
}

function showUploadModal(e) {
    e.preventDefault();
    $('.upload-modal').show();
    $('.file-input').bind('change', startUpload);
    $('.upload-modal .choose-file-button').bind('click', showFileSelectionMenu);
    $modalCover.show();
}

function showFileSelectionMenu(e) {
    e.preventDefault();
    $('.file-input').click();
}

function startUpload(e) {
    $('.upload-modal h1').html('Uploading…');
    $('.upload-modal .file-name').html($('.file-input').val());
    $('.upload-modal .choose-file-button').hide();
    $('.upload-modal .progress-bar').removeClass('loaded').show();
    $('.upload-modal .progress-fill').html('').css('width', '0').animate({
        'width': '100%'
    }, 1500);
    setTimeout(markAsLoaded, 1500);
}

function markAsLoaded() {
    $('.upload-modal .copy-button').css('display', 'inline-block');
    $('.upload-modal .progress-bar').addClass('loaded');
    $('.upload-modal .progress-fill').html('loaded successfully');
    $('.upload-modal .choose-file-button').html('Load Another File').show();
}

function hideModal(e) {
    e.preventDefault();
    $('.modal').hide();
    $modalCover.hide();
}

function onKeyUp(e) {
    if(e.which == 87) {
        $body.toggleClass('show-wip');
    }
}

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






