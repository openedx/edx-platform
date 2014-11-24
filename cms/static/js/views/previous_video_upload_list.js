"use strict";
define(
    ["jquery", "underscore", "backbone", "js/views/baseview", "js/views/previous_video_upload"],
    function($, _, Backbone, BaseView, PreviousVideoUploadView) {
        var PreviousVideoUploadListView = BaseView.extend({
            tagName: "section",
            className: "assets-wrapper",

            initialize: function() {
                this.template = this.loadTemplate("previous-video-upload-list");
            },

            render: function() {
                var $el = this.$el;
                $el.html(this.template());
                var $tabBody = $el.find(".js-table-body");
                this.collection.each(function(model) {
                    var itemView = new PreviousVideoUploadView({model: model});
                    $tabBody.append(itemView.render().$el);
                });
                return this;
            },
        });

        return PreviousVideoUploadListView;
    }
);
