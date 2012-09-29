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
    $newComponentChooser = $('.new-component');
    $newComponentButton = $('.new-component-button');

    $('li.component').each(function(idx, element) {
        new CMS.Views.ModuleEdit({
            el: element,
            model: new CMS.Models.Module({
                id: $(element).data('id'),
            })
        });
    });

    $('.expand-collapse-icon').bind('click', toggleSubmodules);
    $('.visibility-options').bind('change', setVisibility);

    $newComponentButton.bind('click', showNewComponentForm);
    $newComponentChooser.find('.new-component-type a').bind('click', showComponentTemplates);

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

function showNewComponentForm(e) {
    e.preventDefault();
    $newComponentItem.addClass('adding');
    $(this).slideUp(150);
    $newComponentChooser.slideDown(150);
}

function showComponentTemplates(e) {
    e.preventDefault();

    var type = $(this).data('type');
    $newComponentChooser.slideUp(250);
    $('.new-component-'+type).slideDown(250);
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






