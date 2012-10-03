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

    $('.expand-collapse-icon').bind('click', toggleSubmodules);
    $('.visibility-options').bind('change', setVisibility);

    $('.unit-history ol a').bind('click', showHistoryModal);
    $modal.bind('click', hideHistoryModal);
    $modalCover.bind('click', hideHistoryModal);
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






