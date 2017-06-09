define([
    'domReady', 'js/views/import', 'jquery', 'gettext', 'jquery.fileupload', 'jquery.cookie'
], function(domReady, Import, $, gettext) {
    'use strict';

    return function(feedbackUrl, library) {
        var dbError;

        if (library) {
            dbError = gettext('There was an error while importing the new library to our database.');
        } else {
            dbError = gettext('There was an error while importing the new course to our database.');
        }

        var bar = $('.progress-bar'),
            fill = $('.progress-fill'),
            submitBtn = $('.submit-button'),
            chooseBtn = $('.view-import .choose-file-button'),
            defaults = [
                gettext('There was an error during the upload process.') + '\n',
                gettext('There was an error while unpacking the file.') + '\n',
                gettext('There was an error while verifying the file you submitted.') + '\n',
                dbError + '\n'
            ],
            unloading = false,
            previousImport = Import.storedImport(),
            file;

        var onComplete = function() {
            bar.hide();
            chooseBtn
                .find('.copy').html(gettext('Choose new file')).end()
                .show();
        };

        $(window).on('beforeunload', function(event) { unloading = true; });

        // Display the status of last file upload on page load
        if (previousImport) {
            $('.file-name-block')
                .find('.file-name').html(previousImport.file.name).end()
                .show();

            if (previousImport.completed !== true) {
                chooseBtn.hide();
            }

            Import.resume().then(onComplete);
        }

        $('#fileupload').fileupload({
            dataType: 'json',
            type: 'POST',
            maxChunkSize: 20 * 1000000, // 20 MB
            autoUpload: false,
            add: function(e, data) {
                Import.reset();
                submitBtn.unbind('click');

                file = data.files[0];

                if (file.name.match(/tar\.gz$/)) {
                    submitBtn.click(function(event) {
                        event.preventDefault();

                        Import.start(
                            file.name,
                            feedbackUrl.replace('fillerName', file.name)
                        ).then(onComplete);

                        submitBtn.hide();
                        data.submit().complete(function(result, textStatus, xhr) {
                            if (xhr.status !== 200) {
                                var serverMsg, errMsg, stage;

                                try {
                                    serverMsg = $.parseJSON(result.responseText) || {};
                                } catch (e) {
                                    return;
                                }

                                errMsg = serverMsg.hasOwnProperty('ErrMsg') ? serverMsg.ErrMsg : '';

                                if (serverMsg.hasOwnProperty('Stage')) {
                                    stage = Math.abs(serverMsg.Stage);
                                    Import.cancel(defaults[stage] + errMsg, stage);
                                }
                                // It could be that the user is simply refreshing the page
                                // so we need to be sure this is an actual error from the server
                                else if (!unloading) {
                                    $(window).off('beforeunload.import');

                                    Import.reset();
                                    onComplete();

                                    alert(gettext('Your import has failed.') + '\n\n' + errMsg);
                                }
                            }
                        });
                    });
                } else {
                    data.files = [];
                }
            },

            progressall: function(e, data) {
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

                    // Start feedback with delay so that current stage of
                    // import properly updates in session
                    setTimeout(function() { Import.pollStatus(); }, 3000);
                } else {
                    bar.show();
                    fill.width(percentVal).html(percentVal);
                }
            },
            sequentialUploads: true,
            notifyOnError: false
        });


        var showImportSubmit = function(e) {
            var filepath = $(this).val();

            if (filepath.substr(filepath.length - 6, 6) === 'tar.gz') {
                $('.error-block').hide();
                $('.file-name').html($(this).val().replace('C:\\fakepath\\', ''));
                $('.file-name-block').show();
                chooseBtn.hide();
                submitBtn.show();
                $('.progress').show();
            } else {
                var msg = gettext('File format not supported. Please upload a file with a {file_extension} extension.')
                    .replace('{file_extension}', '<code>tar.gz</code>');

                $('.error-block').html(msg).show();
            }
        };

        domReady(function() {
            // import form setup
            $('.view-import .file-input').bind('change', showImportSubmit);
            $('.view-import .choose-file-button, .view-import .choose-file-button-inline').bind('click', function(e) {
                e.preventDefault();
                $('.view-import .file-input').click();
            });
        });
    };
});
