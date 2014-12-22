define(
    ["gettext", "js/utils/date_utils", "js/views/baseview"],
    function(gettext, DateUtils, BaseView) {
        "use strict";

        var statusDisplayStrings = {
            // Translators: This is the status of an active video upload
            UPLOADING: gettext("Uploading"),
            // Translators: This is the status for a video that the servers
            // are currently processing
            IN_PROGRESS: gettext("In Progress"),
            // Translators: This is the status for a video that the servers
            // have successfully processed
            COMPLETE: gettext("Complete"),
            // Translators: This is the status for a video that the servers
            // have failed to process
            FAILED: gettext("Failed"),
            // Translators: This is the status for a video for which an invalid
            // processing token was provided in the course settings
            INVALID_TOKEN: gettext("Invalid Token"),
            // Translators: This is the status for a video that is in an unknown
            // state
            UNKNOWN: gettext("Unknown")
        };

        var statusMap = {
            "upload": statusDisplayStrings.UPLOADING,
            "ingest": statusDisplayStrings.IN_PROGRESS,
            "transcode_queue": statusDisplayStrings.IN_PROGRESS,
            "transcode_active": statusDisplayStrings.IN_PROGRESS,
            "file_delivered": statusDisplayStrings.COMPLETE,
            "file_complete": statusDisplayStrings.COMPLETE,
            "file_corrupt": statusDisplayStrings.FAILED,
            "pipeline_error": statusDisplayStrings.FAILED,
            "invalid_token": statusDisplayStrings.INVALID_TOKEN
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
                    // Translators: This is listed as the duration for a video
                    // that has not yet reached the point in its processing by
                    // the servers where its duration is determined.
                    duration: duration > 0 ? this.renderDuration(duration) : gettext("Pending"),
                    created: DateUtils.renderDate(this.model.get("created")),
                    status: statusMap[this.model.get("status")] || statusDisplayStrings.UNKNOWN
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
