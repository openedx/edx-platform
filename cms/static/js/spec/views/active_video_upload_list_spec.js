"use strict";
define(
    ["jquery", "js/models/active_video_upload", "js/views/active_video_upload_list", "mock-ajax", "jasmine-jquery"],
    function($, ActiveVideoUpload, ActiveVideoUploadListView) {
        var concurrentUploadLimit = 2;
        var activeVideoUploadTpl = readFixtures("active-video-upload.underscore");
        var activeVideoUploadListTpl = readFixtures("active-video-upload-list.underscore");

        describe("ActiveVideoUploadListView", function() {
            beforeEach(function() {
                setFixtures($("<script>", {id: "active-video-upload-tpl", type: "text/template"}).text(activeVideoUploadTpl));
                appendSetFixtures($("<script>", {id: "active-video-upload-list-tpl", type: "text/template"}).text(activeVideoUploadListTpl));
                appendSetFixtures(sandbox());
                this.postUrl = "/test/post/url";
                this.uploadButton = $("<button>");
                this.view = new ActiveVideoUploadListView({
                    el: $("#sandbox"),
                    concurrentUploadLimit: concurrentUploadLimit,
                    postUrl: this.postUrl,
                    uploadButton: this.uploadButton
                });
                this.view.render();
                jasmine.Ajax.useMock();
                clearAjaxRequests();
                this.globalAjaxError = jasmine.createSpy();
                $(document).ajaxError(this.globalAjaxError);
            });

            it("should trigger file selection when either the upload button or the drop zone is clicked", function() {
                var clickSpy = jasmine.createSpy();
                clickSpy.andCallFake(function(event) { event.preventDefault(); });
                this.view.$(".js-file-input").on("click", clickSpy);
                this.view.$(".file-drop-area").click();
                expect(clickSpy).toHaveBeenCalled();
                clickSpy.reset();
                this.uploadButton.click();
                expect(clickSpy).toHaveBeenCalled();
            });

            var makeUploadUrl = function(fileName) {
                return "http://www.example.com/test_url/" + fileName;
            }

            var getSentRequests = function() {
                return _.filter(
                    ajaxRequests,
                    function(request) { return request.readyState > 0; }
                );
            }

            _.each(
                [
                    {desc: "a single file", numFiles: 1},
                    {desc: "multiple files", numFiles: 2},
                    {desc: "more files than upload limit", numFiles: 3},
                ],
                function(caseInfo) {
                    var fileNames = _.map(
                        _.range(caseInfo.numFiles),
                        function(i) { return "test" + i + ".mp4";}
                    );

                    describe("on selection of " + caseInfo.desc, function() {
                        beforeEach(function() {
                            // The files property cannot be set on a file input for
                            // security reasons, so we must mock the access mechanism
                            // that jQuery-File-Upload uses to retrieve it.
                            var realProp = $.prop;
                            spyOn($, "prop").andCallFake(function(el, propName) {
                                if (arguments.length == 2 && propName == "files") {
                                    return _.map(
                                        fileNames,
                                        function(fileName) { return {name: fileName}; }
                                    );
                                } else {
                                    realProp.apply(this, arguments);
                                }
                            });
                            this.view.$(".js-file-input").change()
                            this.request = mostRecentAjaxRequest();
                        });

                        it("should trigger the correct request", function() {
                            expect(this.request.url).toEqual(this.postUrl);
                            expect(this.request.method).toEqual("POST");
                            expect(this.request.requestHeaders["Content-Type"]).toEqual("application/json");
                            expect(this.request.requestHeaders["Accept"]).toContain("application/json");
                            expect(JSON.parse(this.request.params)).toEqual({
                                "files": _.map(
                                    fileNames,
                                    function(fileName) { return {"file_name": fileName}; }
                                )
                            });
                        });

                        it("should trigger the global AJAX error handler on server error", function() {
                            this.request.response({status: 500});
                            expect(this.globalAjaxError).toHaveBeenCalled();
                        });

                        describe("and successful server response", function() {
                            beforeEach(function() {
                                clearAjaxRequests();
                                this.request.response({
                                    status: 200,
                                    responseText: JSON.stringify({
                                        files: _.map(
                                            fileNames,
                                            function(fileName) {
                                                return {
                                                    "file-name": fileName,
                                                    "upload-url": makeUploadUrl(fileName)
                                                };
                                            }
                                        )
                                    })
                                });
                                this.$uploadElems = this.view.$(".video-upload-item");
                            });

                            it("should start uploads", function() {
                                var spec = this;
                                var sentRequests = getSentRequests();
                                expect(sentRequests.length).toEqual(
                                    _.min([concurrentUploadLimit, caseInfo.numFiles])
                                );
                                _.each(
                                    sentRequests,
                                    function(uploadRequest, i) {
                                        expect(uploadRequest.url).toEqual(
                                            makeUploadUrl(fileNames[i])
                                        );
                                        expect(uploadRequest.method).toEqual("PUT");
                                    }
                                );
                            });

                            it("should display status", function() {
                                var spec = this;
                                expect(this.$uploadElems.length).toEqual(caseInfo.numFiles);
                                this.$uploadElems.each(function(i, uploadElem) {
                                    var $uploadElem = $(uploadElem);
                                    expect($.trim($uploadElem.find(".video-detail-title").text())).toEqual(
                                        fileNames[i]
                                    );
                                    expect($.trim($uploadElem.find(".status-message").text())).toEqual(
                                        i >= concurrentUploadLimit ?
                                            ActiveVideoUpload.STATUS_QUEUED :
                                            ActiveVideoUpload.STATUS_UPLOADING
                                    );
                                    expect($uploadElem.find(".success")).not.toExist();
                                    expect($uploadElem.find(".error")).not.toExist();
                                });
                            });

                            _.each(
                                [
                                    {
                                        desc: "completion",
                                        responseStatus: 204,
                                        statusText: ActiveVideoUpload.STATUS_COMPLETED,
                                        presentSelector: ".success",
                                        absentSelector: ".error"
                                    },
                                    {
                                        desc: "failure",
                                        responseStatus: 500,
                                        statusText: ActiveVideoUpload.STATUS_FAILED,
                                        presentSelector: ".error",
                                        absentSelector: ".success"
                                    },
                                ],
                                function(subCaseInfo) {
                                    describe("and upload " + subCaseInfo.desc, function() {
                                        beforeEach(function() {
                                            getSentRequests()[0].response({status: subCaseInfo.responseStatus});
                                        });

                                        it("should update status", function() {
                                            var $uploadElem = $(".video-upload-item:first");
                                            expect($uploadElem.length).toEqual(1);
                                            expect($.trim($uploadElem.find(".status-message").text())).toEqual(
                                                subCaseInfo.statusText
                                            );
                                            expect($uploadElem.find(subCaseInfo.presentSelector)).toExist();
                                            expect($uploadElem.find(subCaseInfo.absentSelector)).not.toExist();
                                        });

                                        it("should not trigger the global AJAX error handler", function() {
                                            expect(this.globalAjaxError).not.toHaveBeenCalled();
                                        });

                                        if (caseInfo.numFiles > concurrentUploadLimit) {
                                            it("should start a new upload", function() {
                                                expect(getSentRequests().length).toEqual(
                                                    concurrentUploadLimit + 1
                                                );
                                                var $uploadElem = $(this.$uploadElems[concurrentUploadLimit]);
                                                expect($.trim($uploadElem.find(".status-message").text())).toEqual(
                                                    ActiveVideoUpload.STATUS_UPLOADING
                                                );
                                            });
                                        }
                                    });
                                }
                            );
                        });
                    });
                }
            );
        });
    }
);
