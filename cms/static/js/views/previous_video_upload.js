"use strict";
define(
    ["i18n", "js/views/baseview"],
    function(i18n, BaseView) {
        var statusMap = {
            "upload": i18n.gettext("Uploading"),
            "ingest": i18n.gettext("In Progress"),
            "transcode_queue": i18n.gettext("In Progress"),
            "transcode_active": i18n.gettext("In Progress"),
            "file_delivered": i18n.gettext("Complete"),
            "file_complete": i18n.gettext("Complete"),
            "file_corrupt": i18n.gettext("Failed"),
            "pipeline_error": i18n.gettext("Failed"),
            "invalid_token": i18n.gettext("Invalid Token")
        };

        var PreviousVideoUploadView = BaseView.extend({
            tagName: "tr",

            initialize: function() {
                this.template = this.loadTemplate("previous-video-upload");
            },

            renderDuration: function(seconds) {
                var minutes = Math.floor(seconds/ 60);
                var seconds = Math.floor(seconds - minutes * 60);

                return minutes + ":" + (seconds < 10 ? "0" : "") + seconds;
            },

            render: function() {
                var duration = this.model.get("duration");
                var renderedAttributes = {
                    // Translators: This is listed as the duration for a video that has not yet
                    // gotten far enough in the pipeline to have had its duration determined.
                    duration: duration > 0 ? this.renderDuration(duration) : i18n.gettext("Pending"),
                    created: Date.parse(this.model.get("created")).toLocaleString(
                        [],
                        {timeZone: "UTC", timeZoneName: "short"}
                    ),
                    // Translators: This is the status label for a video upload with a status
                    // that is not known.
                    status: statusMap[this.model.get("status")] || i18n.gettext("Unknown")
                };
                this.$el.html(
                    this.template(_.extend({}, this.model.attributes, renderedAttributes))
                );
                return this;
            }
        });

        return PreviousVideoUploadView;
    }
);
