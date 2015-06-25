define([
    'js/views/import', 'jquery', 'gettext', 'jquery.fileupload', 'jquery.cookie'
], function(Import, $, gettext) {
    'use strict';
    return function (feedbackUrl, library) {
        var dbError;
        if (library) {
            dbError = gettext('There was an error while importing the new library to our database.');
        } else {
            dbError = gettext('There was an error while importing the new course to our database.');
        }
        var bar = $('.progress-bar'),
            fill = $('.progress-fill'),
            submitBtn = $('.submit-button'),
            chooseBtn = $('.choose-file-button'),
            defaults = [
                gettext('There was an error during the upload process.') + '\n',
                gettext('There was an error while unpacking the file.') + '\n',
                gettext('There was an error while verifying the file you submitted.') + '\n',
                dbError + '\n'
            ],
            // Display the status of last file upload on page load
            lastFileUpload = $.cookie('lastfileupload'),
            file;

        if (lastFileUpload){
            Import.getAndStartUploadFeedback(feedbackUrl.replace('fillerName', lastFileUpload), lastFileUpload);
        }

        $('#fileupload').fileupload({
            dataType: 'json',
            type: 'POST',
            maxChunkSize: 20 * 1000000, // 20 MB
            autoUpload: false,
            add: function(e, data) {
                Import.clearImportDisplay();
                Import.okayToNavigateAway = false;
                submitBtn.unbind('click');
                file = data.files[0];
                if (file.name.match(/tar\.gz$/)) {
                    submitBtn.click(function(event){
                        event.preventDefault();
                        $.cookie('lastfileupload', file.name);
                        submitBtn.hide();
                        Import.startUploadFeedback();
                        data.submit().complete(function(result, textStatus, xhr) {
                            window.onbeforeunload = null;
                            if (xhr.status != 200) {
                                var serverMsg, errMsg, stage;
                                try{
                                    serverMsg = $.parseJSON(result.responseText);
                                } catch (e) {
                                    return;
                                }
                                errMsg = serverMsg.hasOwnProperty('ErrMsg') ?  serverMsg.ErrMsg : '' ;
                                if (serverMsg.hasOwnProperty('Stage')) {
                                    stage = Math.abs(serverMsg.Stage);
                                    Import.stageError(stage, defaults[stage] + errMsg);
                                }
                                else {
                                    alert(gettext('Your import has failed.') + '\n\n' + errMsg);
                                }
                                chooseBtn.html(gettext('Choose new file')).show();
                                bar.hide();
                            }
                            Import.stopGetStatus = true;
                            chooseBtn.html(gettext('Choose new file')).show();
                            bar.hide();
                        });
                    });
                } else {
                    data.files = [];
                }
            },

            progressall: function(e, data){
                var percentInt = data.loaded / data.total * 100,
                    percentVal = parseInt(percentInt, 10) + '%',
                    doneAt;
                // Firefox makes ProgressEvent.loaded equal ProgressEvent.total only
                // after receiving a response from the server (see Mozilla bug 637002),
                // so for Firefox we jump the gun a little.
                if (navigator.userAgent.toLowerCase().indexOf('firefox') > -1) {
                    doneAt = 95;
                } else {
                    doneAt = 99;
                }
                if (percentInt >= doneAt) {
                    bar.hide();
                    // Start feedback with delay so that current stage of import properly updates in session
                    setTimeout(
                        function () { Import.startServerFeedback(feedbackUrl.replace('fillerName', file.name));},
                        3000
                    );
                } else {
                    bar.show();
                    fill.width(percentVal).html(percentVal);
                }
            },
            done: function(event, data){
                bar.hide();
                window.onbeforeunload = null;
                Import.displayFinishedImport();
            },
            start: function(event) {
                window.onbeforeunload = function() {
                    if (!Import.okayToNavigateAway) {
                        return "${_('Your import is in progress; navigating away will abort it.')}";
                    }
                };
            },
            sequentialUploads: true,
            notifyOnError: false
        });
    };
});
