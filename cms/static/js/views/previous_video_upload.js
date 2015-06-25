define(
    ["gettext", "js/utils/date_utils", "js/views/baseview"],
    function(gettext, DateUtils, BaseView) {
        "use strict";

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
                    status: this.model.get("status")
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
