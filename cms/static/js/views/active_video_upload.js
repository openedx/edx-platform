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
                var $statusEl = this.$el.find(".video-detail-status");
                var status = this.model.get("status");
                $statusEl.toggleClass("success", status == ActiveVideoUpload.STATUS_COMPLETED);
                $statusEl.toggleClass("error", status == ActiveVideoUpload.STATUS_FAILED);
                return this;
            },
        });

        return ActiveVideoUploadView;
    }
);
