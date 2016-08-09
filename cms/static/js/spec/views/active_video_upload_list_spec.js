define(
    [
        'jquery',
        'js/models/active_video_upload',
        'js/views/active_video_upload_list',
        'common/js/spec_helpers/template_helpers',
        'mock-ajax'
    ],
    function($, ActiveVideoUpload, ActiveVideoUploadListView, TemplateHelpers) {
        'use strict';
        var concurrentUploadLimit = 2;

        describe('ActiveVideoUploadListView', function() {
            beforeEach(function() {
                TemplateHelpers.installTemplate('active-video-upload', true);
                TemplateHelpers.installTemplate('active-video-upload-list');
                this.postUrl = '/test/post/url';
                this.uploadButton = $('<button>');
                this.view = new ActiveVideoUploadListView({
                    concurrentUploadLimit: concurrentUploadLimit,
                    postUrl: this.postUrl,
                    uploadButton: this.uploadButton
                });
                this.view.render();
                jasmine.Ajax.install();
                this.globalAjaxError = jasmine.createSpy();
                $(document).ajaxError(this.globalAjaxError);
            });

            // Remove window unload handler triggered by the upload requests
            afterEach(function() {
                $(window).off('beforeunload');
                jasmine.Ajax.uninstall();
            });

            it('should trigger file selection when either the upload button or the drop zone is clicked', function() {
                var clickSpy = jasmine.createSpy();
                clickSpy.and.callFake(function(event) { event.preventDefault(); });
                this.view.$('.js-file-input').on('click', clickSpy);
                this.view.$('.file-drop-area').click();
                expect(clickSpy).toHaveBeenCalled();
                clickSpy.calls.reset();
                this.uploadButton.click();
                expect(clickSpy).toHaveBeenCalled();
            });

            it('should not show a notification message if there are no active video uploads', function() {
                expect(this.view.onBeforeUnload()).toBeUndefined();
            });

            var makeUploadUrl = function(fileName) {
                return 'http://www.example.com/test_url/' + fileName;
            };

            var getSentRequests = function() {
                return jasmine.Ajax.requests.filter(function(request) {
                    return request.readyState > 0;
                });
            };

            _.each(
                [
                    {desc: 'a single file', numFiles: 1},
                    {desc: 'multiple files', numFiles: concurrentUploadLimit},
                    {desc: 'more files than upload limit', numFiles: concurrentUploadLimit + 1}
                ],
                function(caseInfo) {
                    var fileNames = _.map(
                        _.range(caseInfo.numFiles),
                        function(i) { return 'test' + i + '.mp4'; }
                    );

                    describe('on selection of ' + caseInfo.desc, function() {
                        beforeEach(function() {
                            // The files property cannot be set on a file input for
                            // security reasons, so we must mock the access mechanism
                            // that jQuery-File-Upload uses to retrieve it.
                            var realProp = $.prop;
                            spyOn($, 'prop').and.callFake(function(el, propName) {
                                if (arguments.length == 2 && propName == 'files') {
                                    return _.map(
                                        fileNames,
                                        function(fileName) { return {name: fileName}; }
                                    );
                                } else {
                                    realProp.apply(this, arguments);
                                }
                            });
                            this.view.$('.js-file-input').change();
                            this.request = jasmine.Ajax.requests.mostRecent();
                        });

                        it('should trigger the correct request', function() {
                            expect(this.request.url).toEqual(this.postUrl);
                            expect(this.request.method).toEqual('POST');
                            expect(this.request.requestHeaders['Content-Type']).toEqual('application/json');
                            expect(this.request.requestHeaders['Accept']).toContain('application/json');
                            expect(JSON.parse(this.request.params)).toEqual({
                                'files': _.map(
                                    fileNames,
                                    function(fileName) { return {'file_name': fileName}; }
                                )
                            });
                        });

                        it('should trigger the global AJAX error handler on server error', function() {
                            this.request.respondWith({status: 500});
                            expect(this.globalAjaxError).toHaveBeenCalled();
                        });

                        describe('and successful server response', function() {
                            beforeEach(function() {
                                jasmine.Ajax.requests.reset();
                                this.request.respondWith({
                                    status: 200,
                                    responseText: JSON.stringify({
                                        files: _.map(
                                            fileNames,
                                            function(fileName) {
                                                return {
                                                    'file_name': fileName,
                                                    'upload_url': makeUploadUrl(fileName)
                                                };
                                            }
                                        )
                                    })
                                });
                                this.$uploadElems = this.view.$('.active-video-upload');
                            });

                            it('should start uploads', function() {
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
                                        expect(uploadRequest.method).toEqual('PUT');
                                    }
                                );
                            });

                            it('should display upload status and progress', function() {
                                expect(this.$uploadElems.length).toEqual(caseInfo.numFiles);
                                this.$uploadElems.each(function(i, uploadElem) {
                                    var $uploadElem = $(uploadElem);
                                    var queued = i >= concurrentUploadLimit;
                                    expect($.trim($uploadElem.find('.video-detail-name').text())).toEqual(
                                        fileNames[i]
                                    );
                                    expect($.trim($uploadElem.find('.video-detail-status').text())).toEqual(
                                        queued ?
                                            ActiveVideoUpload.STATUS_QUEUED :
                                            ActiveVideoUpload.STATUS_UPLOADING
                                    );
                                    expect($uploadElem.find('.video-detail-progress').val()).toEqual(0);
                                    expect($uploadElem).not.toHaveClass('success');
                                    expect($uploadElem).not.toHaveClass('error');
                                    expect($uploadElem.hasClass('queued')).toEqual(queued);
                                });
                            });

                            it('should show a notification message when there are active video uploads', function() {
                                expect(this.view.onBeforeUnload()).toBe('Your video uploads are not complete.');
                            });

                            // TODO: test progress update; the libraries we are using to mock ajax
                            // do not currently support progress events. If we upgrade to Jasmine
                            // 2.0, the latest version of jasmine-ajax (mock-ajax.js) does have the
                            // necessary support.

                            _.each(
                                [
                                    {
                                        desc: 'completion',
                                        responseStatus: 204,
                                        statusText: ActiveVideoUpload.STATUS_COMPLETED,
                                        progressValue: 1,
                                        presentClass: 'success',
                                        absentClass: 'error'
                                    },
                                    {
                                        desc: 'failure',
                                        responseStatus: 500,
                                        statusText: ActiveVideoUpload.STATUS_FAILED,
                                        progressValue: 0,
                                        presentClass: 'error',
                                        absentClass: 'success'
                                    }
                                ],
                                function(subCaseInfo) {
                                    describe('and upload ' + subCaseInfo.desc, function() {
                                        beforeEach(function() {
                                            getSentRequests()[0].respondWith({status: subCaseInfo.responseStatus});
                                        });

                                        it('should update status and progress', function() {
                                            var $uploadElem = this.view.$('.active-video-upload:first');
                                            expect($uploadElem.length).toEqual(1);
                                            expect($.trim($uploadElem.find('.video-detail-status').text())).toEqual(
                                                subCaseInfo.statusText
                                            );
                                            expect(
                                                $uploadElem.find('.video-detail-progress').val()
                                            ).toEqual(subCaseInfo.progressValue);
                                            expect($uploadElem).toHaveClass(subCaseInfo.presentClass);
                                            expect($uploadElem).not.toHaveClass(subCaseInfo.absentClass);
                                        });

                                        it('should not trigger the global AJAX error handler', function() {
                                            expect(this.globalAjaxError).not.toHaveBeenCalled();
                                        });

                                        if (caseInfo.numFiles > concurrentUploadLimit) {
                                            it('should start a new upload', function() {
                                                expect(getSentRequests().length).toEqual(
                                                    concurrentUploadLimit + 1
                                                );
                                                var $uploadElem = $(this.$uploadElems[concurrentUploadLimit]);
                                                expect($.trim($uploadElem.find('.video-detail-status').text())).toEqual(
                                                    ActiveVideoUpload.STATUS_UPLOADING
                                                );
                                                expect($uploadElem).not.toHaveClass('queued');
                                            });
                                        }

                                        // If we're uploading more files than the one we've closed above,
                                        // the unload warning should still be shown
                                        if (caseInfo.numFiles > 1) {
                                            it('should show notification when videos are still uploading',
                                                function() {
                                                    expect(this.view.onBeforeUnload()).toBe(
                                                        'Your video uploads are not complete.');
                                                });
                                        } else {
                                            it('should not show notification once video uploads are complete',
                                                function() {
                                                    expect(this.view.onBeforeUnload()).toBeUndefined();
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
