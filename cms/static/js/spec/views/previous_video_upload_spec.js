define(
    ["jquery", "backbone", "js/views/previous_video_upload", "common/js/spec_helpers/template_helpers"],
    function($, Backbone, PreviousVideoUploadView, TemplateHelpers) {
        "use strict";
        describe("PreviousVideoUploadView", function() {
            beforeEach(function() {
                TemplateHelpers.installTemplate("previous-video-upload", true);
            });

            var render = function(modelData) {
                var defaultData = {
                    client_video_id: "foo.mp4",
                    duration: 42,
                    created: "2014-11-25T23:13:05",
                    edx_video_id: "dummy_id",
                    status: "uploading"
                };
                var view = new PreviousVideoUploadView(
                    {model: new Backbone.Model($.extend({}, defaultData, modelData))}
                );
                return view.render().$el;
            };

            it("should render video name correctly", function() {
                var testName = "test name";
                var $el = render({client_video_id: testName});
                expect($el.find(".name-col").text()).toEqual(testName);
            });

            _.each(
                [
                    {desc: "zero as pending", seconds: 0, expected: "Pending"},
                    {desc: "less than one second as zero", seconds: 0.75, expected: "0:00"},
                    {desc: "with minutes and without seconds", seconds: 900, expected: "15:00"},
                    {desc: "with seconds and without minutes", seconds: 15, expected: "0:15"},
                    {desc: "with minutes and seconds", seconds: 915, expected: "15:15"},
                    {desc: "with seconds padded", seconds: 5, expected: "0:05"},
                    {desc: "longer than an hour as many minutes", seconds: 7425, expected: "123:45"}
                ],
                function(caseInfo) {
                    it("should render duration " + caseInfo.desc, function() {
                        var $el = render({duration: caseInfo.seconds});
                        expect($el.find(".duration-col").text()).toEqual(caseInfo.expected);
                    });
                }
            );

            it("should render created timestamp correctly", function() {
                var fakeDate = "fake formatted date";
                spyOn(Date.prototype, "toLocaleString").andCallFake(
                    function(locales, options) {
                        expect(locales).toEqual([]);
                        expect(options.timeZone).toEqual("UTC");
                        expect(options.timeZoneName).toEqual("short");
                        return fakeDate;
                    }
                );
                var $el = render({});
                expect($el.find(".date-col").text()).toEqual(fakeDate);
            });

            it("should render video id correctly", function() {
                var testId = "test_id";
                var $el = render({edx_video_id: testId});
                expect($el.find(".video-id-col").text()).toEqual(testId);
            });

            it("should render status correctly", function() {
                var testStatus = "Test Status";
                var $el = render({status: testStatus});
                expect($el.find(".status-col").text()).toEqual(testStatus);
            });
        });
    }
);
