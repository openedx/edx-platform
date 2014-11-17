define(
    ["js/models/active_video_upload", "js/views/baseview"],
    function(ActiveVideoUpload, BaseView) {
        "use strict";
        var ActiveVideoUploadView = BaseView.extend({
            tagName: "li",
            className: "active-video-upload",

            initialize: function() {
                this.template = this.loadTemplate("active-video-upload");
                this.listenTo(this.model, "change", this.render);
            },

            render: function() {
                this.$el.html(this.template(this.model.attributes));
                var statusClass;
                switch (this.model.get("status")) {
                    case ActiveVideoUpload.STATUS_COMPLETED:
                        statusClass = "success";
                        break;
                    case ActiveVideoUpload.STATUS_FAILED:
                        statusClass = "error";
                        break;
                }
                if (statusClass) {
                    this.$el.find(".status-message .text").addClass(statusClass);
                }
                return this;
            },
        });

        return ActiveVideoUploadView;
    }
);
