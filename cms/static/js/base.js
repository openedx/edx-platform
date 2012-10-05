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
    $('.new-unit-item').bind('click', createNewUnit);
    $('.save-subsection').bind('click', saveSubsection);

    // making the unit list sortable
    $('.sortable-unit-list').sortable();
    $('.sortable-unit-list').disableSelection();
    $('.sortable-unit-list').bind('sortstop', onUnitReordered);

    // expand/collapse methods for optional date setters
    $('.set-date').bind('click', showDateSetter);
    $('.remove-date').bind('click', removeDateSetter);

});

// This method only changes the ordering of the child objects in a subsection
function onUnitReordered() {
    var subsection_id = $(this).data('subsection-id');

    var _els = $(this).children('li:.leaf');

    var children = new Array();
    for(var i=0;i<_els.length;i++) {
	el = _els[i];
	children[i] = $(el).data('id');
    }

    // call into server to commit the new order
    $.ajax({
	    url: "/save_item",
		type: "POST",
		dataType: "json",
		contentType: "application/json",
		data:JSON.stringify({ 'id' : subsection_id, 'metadata' : null, 'data': null, 'children' : children})
	});
}

function getEdxTimeFromDateTimeInputs(date_id, time_id, format) {
    var input_date = $('#'+date_id).val();
    var input_time = $('#'+time_id).val();

    var edxTimeStr = null;

    if (input_date != '') {
        if (input_time == '') 
            input_time = '00:00';

        // Note, we are using date.js utility which has better parsing abilities than the built in JS date parsing
        date = Date.parse(input_date+" "+input_time);
        if (format == null)
            format = 'yyyy-MM-ddTHH:mm';

        edxTimeStr = date.toString(format);
    }

    return edxTimeStr;
}

function saveSubsection(e) {
    e.preventDefault();
    
    var id = $(this).data('id');

    // pull all metadata editable fields on page
    var metadata_fields = $('input[data-metadata-name]');
    
    metadata = {};
    for(var i=0; i< metadata_fields.length;i++) {
	   el = metadata_fields[i];
	   metadata[$(el).data("metadata-name")] = el.value;
    } 

    // OK, we have some metadata (namely 'Release Date' (aka 'start') and 'Due Date') which has been normalized in the UI
    // we have to piece it back together. Unfortunate 'start' and 'due' use different string formatters. Rather than try to 
    // replicate the string formatting which is used in the backend here in JS, let's just pass back a unified format
    // and let the server re-format into the expected persisted format

    metadata['start'] = getEdxTimeFromDateTimeInputs('start_date', 'start_time');
    metadata['due'] = getEdxTimeFromDateTimeInputs('due_date', 'due_time', 'MMMM dd HH:mm');

    // reordering is done through immediate callbacks when the resorting has completed in the UI
    children =[];

    $.ajax({
	    url: "/save_item",
		type: "POST",
		dataType: "json",
		contentType: "application/json",
		data:JSON.stringify({ 'id' : id, 'metadata' : metadata, 'data': null, 'children' : children}),
		success: function() {
		alert('Your changes have been saved.');
	    },
		error: function() {
		alert('There has been an error while saving your changes.');
	    }
	});
}

function createNewUnit(e) {
    e.preventDefault();

    parent = $(this).data('parent');
    template = $(this).data('template');

    $.post('/clone_item',
	   {'parent_location' : parent,
		   'template' : template,
		   'display_name': 'New Unit',
		   },
	   function(data) {
	       // redirect to the edit page
	       window.location = "/edit/" + data['id'];
	   });
}

function deleteUnit(e) {
    e.preventDefault();

    if(!confirm('Are you sure you wish to delete this item. It cannot be reversed!'))
	return;

    var _li_el = $(this).parents('li.leaf');
    var id = _li_el.data('id');
    
    $.post('/delete_item', 
	   {'id': id, 'delete_children' : true}, 
	   function(data) {
	       _li_el.remove();
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

function showDateSetter(e) {
    e.preventDefault();
    var $block = $(this).closest('.due-date-input');
    $(this).hide();
    $block.find('.date-setter').show();
}

function removeDateSetter(e) {
    e.preventDefault();
    var $block = $(this).closest('.due-date-input');
    $block.find('.date-setter').hide();
    $block.find('.set-date').show();
    // clear out the values
    $block.find('.date').val('');
    $block.find('.time').val('');
}



