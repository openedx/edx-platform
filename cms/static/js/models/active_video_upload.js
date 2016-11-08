define(
    ['backbone', 'gettext'],
    function(Backbone, gettext) {
        'use strict';

        var statusStrings = {
            // Translators: This is the status of a video upload that is queued
            // waiting for other uploads to complete
            STATUS_QUEUED: gettext('Queued'),
            // Translators: This is the status of an active video upload
            STATUS_UPLOADING: gettext('Uploading'),
            // Translators: This is the status of a video upload that has
            // completed successfully
            STATUS_COMPLETED: gettext('Upload completed'),
            // Translators: This is the status of a video upload that has failed
            STATUS_FAILED: gettext('Upload failed')
        };

        var ActiveVideoUpload = Backbone.Model.extend(
            {
                defaults: {
                    videoId: null,
                    status: statusStrings.STATUS_QUEUED,
                    progress: 0
                }
            },
            statusStrings
        );

        return ActiveVideoUpload;
    }
);
