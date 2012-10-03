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
    $newComponentTypePicker.find('.new-component-type a').bind('click', showComponentTemplates);
    $newComponentTypePicker.find('.cancel-button').bind('click', closeNewComponent);
    $newComponentTemplatePickers.find('.new-component-template a').bind('click', saveNewComponent);
    $newComponentTemplatePickers.find('.cancel-button').bind('click', closeNewComponent);

    $('.unit-history ol a').bind('click', showHistoryModal);
    $modal.bind('click', hideModal);
    $modalCover.bind('click', hideHistoryModal);

    $('.assets .upload-button').bind('click', showUploadModal);
    $('.upload-modal .close-button').bind('click', hideModal);
});

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

function showNewComponentForm(e) {
    e.preventDefault();
    $newComponentItem.addClass('adding');
    $(this).slideUp(150);
    $newComponentTypePicker.slideDown(250);
}

function showComponentTemplates(e) {
    e.preventDefault();

    var type = $(this).data('type');
    $newComponentTypePicker.slideUp(250);
    $('.new-component-'+type).slideDown(250);
}

function closeNewComponent(e) {
    e.preventDefault();

    $newComponentTypePicker.slideUp(250);
    $newComponentTemplatePickers.slideUp(250);
    $newComponentButton.slideDown(250);
    $newComponentItem.removeClass('adding');
    $newComponentItem.find('.rendered-component').remove();
}

function saveNewComponent(e) {
    e.preventDefault();

    editor = new CMS.Views.ModuleEdit({
        model: new CMS.Models.Module()
    })

    $newComponentItem.before(editor.$el)

    editor.cloneTemplate($(this).data('location'))

    closeNewComponent(e);
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






