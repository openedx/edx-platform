"use strict";
define(
    ["jquery", "underscore", "backbone", "js/views/previous_video_upload_list"],
    function($, _, Backbone, PreviousVideoUploadListView) {
        describe("PreviousVideoUploadListView", function() {
            var previousVideoUploadTpl = readFixtures("previous-video-upload.underscore");
            var previousVideoUploadListTpl = readFixtures("previous-video-upload-list.underscore");

            beforeEach(function() {
                setFixtures($("<script>", {id: "previous-video-upload-tpl", type: "text/template"}).text(previousVideoUploadTpl));
                appendSetFixtures($("<script>", {id: "previous-video-upload-list-tpl", type: "text/template"}).text(previousVideoUploadListTpl));
            });

            var render = function(numModels) {
                var modelData = {
                    client_video_id: "foo.mp4",
                    duration: 42,
                    created: "2014-11-25T23:13:05",
                    edx_video_id: "dummy_id",
                    status: "uploading"
                };
                var collection = new Backbone.Collection(
                    _.map(
                        _.range(numModels),
                        function() { return new Backbone.Model(modelData); }
                    )
                );
                var view = new PreviousVideoUploadListView({collection: collection});
                return view.render().$el;
            };

            it("should render an empty collection", function() {
                var $el = render(0);
                expect($el.find(".js-table-body").length).toEqual(1);
                expect($el.find(".js-table-body tr").length).toEqual(0);
            });

            it("should render a non-empty collection", function() {
                var $el = render(5);
                expect($el.find(".js-table-body").length).toEqual(1);
                expect($el.find(".js-table-body tr").length).toEqual(5);
            });
        });
    }
);
