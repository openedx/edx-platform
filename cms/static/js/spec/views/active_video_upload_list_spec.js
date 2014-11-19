"use strict";
define(
    ["jquery", "js/models/active_video_upload", "js/views/active_video_upload_list", "mock-ajax", "jasmine-jquery"],
    function($, ActiveVideoUpload, ActiveVideoUploadListView) {
        var activeVideoUploadTpl = readFixtures("active-video-upload.underscore");
        var activeVideoUploadListTpl = readFixtures("active-video-upload-list.underscore");

        describe("ActiveVideoUploadListView", function() {
            beforeEach(function() {
                setFixtures($("<script>", {id: "active-video-upload-tpl", type: "text/template"}).text(activeVideoUploadTpl));
                appendSetFixtures($("<script>", {id: "active-video-upload-list-tpl", type: "text/template"}).text(activeVideoUploadListTpl));
                appendSetFixtures(sandbox());
                this.view = new ActiveVideoUploadListView({el: $("#sandbox")});
                this.view.render();
            });

            it("upload button should trigger file selection", function() {
                var clickSpy = jasmine.createSpy();
                clickSpy.andCallFake(function(event) { event.preventDefault(); });
                this.view.$(".js-file-input").on("click", clickSpy);
                this.view.$(".js-upload-button").click();
                expect(clickSpy).toHaveBeenCalled();
            });

            describe("on file selection", function() {
                beforeEach(function() {
                    jasmine.Ajax.useMock();
                    // The files property cannot be set on a file input for
                    // security reasons, so we must mock the access mechanism
                    // that jQuery-File-Upload uses to retrieve it.
                    var realProp = $.prop;
                    spyOn($, "prop").andCallFake(function(el, propName) {
                        if (arguments.length == 2 && propName == "files") {
                            return [{name: "test_video.mp4"}]
                        } else {
                            realProp.apply(this, arguments);
                        }
                    });
                    this.view.$(".js-file-input").change()
                    this.request = mostRecentAjaxRequest();
                });

                it("the correct request is triggered", function() {
                    expect(this.request.url).toEqual(window.location.href);
                    expect(this.request.method).toEqual("POST");
                    expect(this.request.requestHeaders["Content-Type"]).toEqual("application/json");
                    expect(this.request.requestHeaders["Accept"]).toContain("application/json");
                    expect(JSON.parse(this.request.params)).toEqual({
                        "files": [{"file-name": "test_video.mp4"}]
                    });
                });

                it("server failure should trigger the global AJAX error handler", function() {
                    var globalAjaxError = jasmine.createSpy();
                    $(document).ajaxError(globalAjaxError);
                    this.request.response({status: 500});
                    expect(globalAjaxError).toHaveBeenCalled();
                });

                describe("and successful server response", function() {
                    beforeEach(function() {
                        this.request.response({
                            status: 200,
                            responseText: JSON.stringify({
                                files: [{"upload-url": "https://www.example.com/test_url"}]
                            })
                        });
                        this.uploadRequest = mostRecentAjaxRequest();
                        this.$uploadEl = this.view.$(".js-active-video-upload-list > li");
                    });

                    it("should start upload, update its collection, and show status", function() {
                        expect(this.uploadRequest.url).toEqual("https://www.example.com/test_url");
                        expect(this.uploadRequest.method).toEqual("PUT");
                        expect(this.view.collection.length).toEqual(1);
                        expect(this.view.collection.at(0).get("status")).toEqual(
                            ActiveVideoUpload.STATUS_UPLOADING
                        );
                        expect(this.$uploadEl.length).toEqual(1);
                        expect($.trim(this.$uploadEl.find(".status-message").text())).toEqual(
                            ActiveVideoUpload.STATUS_UPLOADING
                        );
                        expect(this.$uploadEl.find(".success")).not.toExist();
                        expect(this.$uploadEl.find(".error")).not.toExist();
                    });

                    it("should update status to completed on upload completion", function() {
                        this.uploadRequest.response({status: 204});
                        expect(this.view.collection.at(0).get("status")).toEqual(
                            ActiveVideoUpload.STATUS_COMPLETED
                        );
                        expect(this.$uploadEl.length).toEqual(1);
                        expect($.trim(this.$uploadEl.find(".status-message").text())).toEqual(
                            ActiveVideoUpload.STATUS_COMPLETED
                        );
                        expect(this.$uploadEl.find(".success")).toExist();
                        expect(this.$uploadEl.find(".error")).not.toExist();
                    });

                    it("should update status to failed on upload failure", function() {
                        this.uploadRequest.response({status: 500});
                        expect(this.view.collection.at(0).get("status")).toEqual(
                            ActiveVideoUpload.STATUS_FAILED
                        );
                        expect(this.$uploadEl.length).toEqual(1);
                        expect($.trim(this.$uploadEl.find(".status-message").text())).toEqual(
                            ActiveVideoUpload.STATUS_FAILED
                        );
                        expect(this.$uploadEl.find(".success")).not.toExist();
                        expect(this.$uploadEl.find(".error")).toExist();
                    });
                });
            });
        });
    }
);
