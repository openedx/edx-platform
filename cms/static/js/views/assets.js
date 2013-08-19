$(document).ready(function() {
    $('.uploads .upload-button').bind('click', showUploadModal);
    $('.upload-modal .close-button').bind('click', resetUploadModal);
    $('.upload-modal .choose-file-button').bind('click', showFileSelectionMenu);
    $('.remove-asset-button').bind('click', removeAsset);
});

function removeAsset(e){
    e.preventDefault();

    var that = this;
    var msg = new CMS.Views.Prompt.Warning({
        title: gettext("Delete File Confirmation"),
        message: gettext("Are you sure you wish to delete this item. It cannot be reversed!\n\nAlso any content that links/refers to this item will no longer work (e.g. broken images and/or links)"),
        actions: {
            primary: {
                text: gettext("OK"),
                click: function(view) {
                    // call the back-end to actually remove the asset
                    var url = $('.asset-library').data('remove-asset-callback-url');
                    var row = $(that).closest('tr');
                    $.post(url,
                        { 'location': row.data('id') },
                        function() {
                            // show the post-commit confirmation
                            var deleted = new CMS.Views.Notification.Confirmation({
                                title: gettext("Your file has been deleted."),
                                closeIcon: false,
                                maxShown: 2000
                            });
                            deleted.show();
                            row.remove();
                            analytics.track('Deleted Asset', {
                                'course': course_location_analytics,
                                'id': row.data('id')
                            });
                        }
                    );
                    view.hide();
                }
            },
            secondary: [{
                text: gettext("Cancel"),
                click: function(view) {
                    view.hide();
                }
            }]
        }
    });
    return msg.show();
}

function showUploadModal(e) {
    e.preventDefault();
    resetUploadBar();
    $modal = $('.upload-modal').show();
    $('.upload-modal .file-chooser').fileupload({
        dataType: 'json',
        type: 'POST',
        maxChunkSize: 100 * 1000 * 1000,      // 100 MB
        autoUpload: true,
        progressall: function(e, data) {
            var percentComplete = parseInt(data.loaded / data.total * 100, 10);
            showUploadFeedback(e, percentComplete);
        },
        maxFileSize: 10 * 1000 * 1000,   // 100 MB
        maxNumberofFiles: 30,
        add: function(e, data) {
            // Uncomment this line to get html template on load
            // var html = assetUploadTemplate(data.files);
            data.process().done(function () {
                data.submit();
            });
        },
        done: function(e, data) {
            displayFinishedUpload(data.result);
        }

    });
    $('.file-input').bind('change', startUpload);
    $modalCover.show();
}

function assetUploadTemplate(files) {
    var compiled = _.template('<tr class="modal-asset>' +
               '<td><span class="modal-asset new"></span></td>' +
                '<td><p class="modal-asset name"> <%= file.name %></td>' +
                '</tr>');
    var html = '';
    for (var i=0; i < files.length; i++) {
        html += compiled({ file: files[i]});
    }
    return html;
}

function showFileSelectionMenu(e) {
    e.preventDefault();
    $('.file-input').click();
}

function startUpload(e) {
    var files = $('.file-input').get(0).files;
    if (files.length === 0)
        return;

    $('.upload-modal h1').html(gettext('Uploading…'));
    $('.upload-modal .file-name').html(files[0].name);
    $('.upload-modal .choose-file-button').hide();
    $('.upload-modal .progress-bar').removeClass('loaded').show();
}

function resetUploadBar() {
    var percentVal = '0%';
    $('.upload-modal .progress-fill').width(percentVal);
    $('.upload-modal .progress-fill').html(percentVal);
}

function resetUploadModal() {
    resetUploadBar();
    $('.upload-modal .file-name').html('');
    $('.upload-modal h1').html(gettext('Upload New File'));
    $('.upload-modal .choose-file-button').html(gettext('Choose File'));
    $('.upload-modal .embeddable-xml-input').val('');
    $('.upload-modal .embeddable').hide();
    hideModal();
}

function showUploadFeedback(event, percentComplete) {
    var percentVal = percentComplete + '%';
    $('.upload-modal .progress-fill').width(percentVal);
    $('.upload-modal .progress-fill').html(percentVal);
}

function displayFinishedUpload(resp) {
    if (resp.status == 200) {
        markAsLoaded();
    }

    $('.upload-modal .embeddable-xml-input').val(resp.portable_url);
    $('.upload-modal .embeddable').show();
    $('.upload-modal .file-name').hide();
    $('.upload-modal .progress-fill').html(resp.msg);
    $('.upload-modal .choose-file-button').html(gettext('Load Another File')).show();
    $('.upload-modal .progress-fill').width('100%');

    // see if this id already exists, if so, then user must have updated an existing piece of content
    $("tr[data-id='" + resp.url + "']").remove();

    var template = $('#new-asset-element').html();
    var html = Mustache.to_html(template, resp);
    $('table > tbody').prepend(html);

    // re-bind the listeners to delete it
    $('.remove-asset-button').bind('click', removeAsset);

    analytics.track('Uploaded a File', {
        'course': course_location_analytics,
        'asset_url': resp.url
    });
}
