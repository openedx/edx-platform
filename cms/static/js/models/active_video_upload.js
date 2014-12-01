"use strict";
define(
    ["backbone", "i18n"],
    function(Backbone, i18n) {

        var STATUS_QUEUED = i18n.gettext_noop("Queued");
        var STATUS_UPLOADING = i18n.gettext_noop("Uploading");
        var STATUS_COMPLETED = i18n.gettext_noop("Upload completed");
        var STATUS_FAILED = i18n.gettext_noop("Upload failed");

        var ActiveVideoUpload = Backbone.Model.extend(
            {
                defaults: {
                    status: STATUS_QUEUED
                }
            },
            {
                STATUS_QUEUED: STATUS_QUEUED,
                STATUS_UPLOADING: STATUS_UPLOADING,
                STATUS_COMPLETED: STATUS_COMPLETED,
                STATUS_FAILED: STATUS_FAILED
            }
        );

        return ActiveVideoUpload;
    }
);
