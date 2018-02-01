define([
    'domReady', 'js/views/export', 'jquery', 'gettext'
], function(domReady, Export, $, gettext) {
    'use strict';
    return function(courselikeHomeUrl, library, statusUrl) {
        var $submitBtn = $('.action-export'),
            $videosCheckbox = $('.action-include-videos'),
            unloading = false,
            previousExport = Export.storedExport(courselikeHomeUrl);

        var onComplete = function() {
            $submitBtn.show();
            $videosCheckbox.show();
        };

        var startExport = function(e) {
            var checkboxName = $videosCheckbox.find('input').attr('name');
            var checkboxVal = $videosCheckbox.find('input').is(':checked');
            var data = {};
            if (checkboxVal) {
                data[checkboxName] = checkboxVal;
            }
            e.preventDefault();
            $submitBtn.hide();
            $videosCheckbox.hide();
            Export.reset(library);
            Export.start(statusUrl).then(onComplete);
            $.ajax({
                type: 'POST',
                url: window.location.pathname,
                data: data,
                success: function(result, textStatus, xhr) {
                    if (xhr.status === 200) {
                        setTimeout(function() { Export.pollStatus(result); }, 1000);
                    } else {
                        // It could be that the user is simply refreshing the page
                        // so we need to be sure this is an actual error from the server
                        if (!unloading) {
                            $(window).off('beforeunload.import');

                            Export.reset(library);
                            onComplete();

                            Export.showError(gettext('Your export has failed.'));
                        }
                    }
                }
            });
        };

        $(window).on('beforeunload', function() { unloading = true; });

        // Display the status of last file upload on page load
        if (previousExport) {
            if (previousExport.completed !== true) {
                $submitBtn.hide();
                $videosCheckbox.hide();
            }
            Export.resume(library).then(onComplete);
        }

        domReady(function() {
            // export form setup
            $submitBtn.bind('click', startExport);
        });
    };
});
