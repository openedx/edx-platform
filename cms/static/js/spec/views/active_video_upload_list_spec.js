/* global _ */
define(
    [
        'jquery',
        'js/models/active_video_upload',
        'js/views/active_video_upload_list',
        'edx-ui-toolkit/js/utils/string-utils',
        'common/js/spec_helpers/template_helpers',
        'edx-ui-toolkit/js/utils/spec-helpers/ajax-helpers',
        'accessibility',
        'mock-ajax'
    ],
    function($, ActiveVideoUpload, ActiveVideoUploadListView, StringUtils, TemplateHelpers, AjaxHelpers) {
        'use strict';
        var concurrentUploadLimit = 2,
            POST_URL = '/test/post/url',
            VIDEO_ID = 'video101',
            UPLOAD_STATUS = {
                s3Fail: 's3_upload_failed',
                fail: 'upload_failed',
                success: 'upload_completed'
            },
            makeUploadUrl,
            getSentRequests,
            verifyUploadViewInfo,
            getStatusUpdateRequest,
            verifyStatusUpdateRequest,
            sendUploadPostResponse,
            verifyA11YMessage,
            verifyUploadPostRequest;

        describe('ActiveVideoUploadListView', function() {
            beforeEach(function() {
                setFixtures(
                    '<div id="page-prompt"></div><div id="page-notification"></div><div id="reader-feedback"></div>'
                );
                TemplateHelpers.installTemplate('active-video-upload');
                TemplateHelpers.installTemplate('active-video-upload-list');
                this.postUrl = POST_URL;
                this.uploadButton = $('<button>');
                this.videoSupportedFileFormats = ['.mp4', '.mov'];
                this.videoUploadMaxFileSizeInGB = 5;
                this.view = new ActiveVideoUploadListView({
                    concurrentUploadLimit: concurrentUploadLimit,
                    postUrl: this.postUrl,
                    uploadButton: this.uploadButton,
                    videoSupportedFileFormats: this.videoSupportedFileFormats,
                    videoUploadMaxFileSizeInGB: this.videoUploadMaxFileSizeInGB
                });
                this.view.render();
                jasmine.Ajax.install();
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

            makeUploadUrl = function(fileName) {
                return 'http://www.example.com/test_url/' + fileName;
            };

            getSentRequests = function() {
                return jasmine.Ajax.requests.filter(function(request) {
                    return request.readyState > 0;
                });
            };

            verifyUploadViewInfo = function(view, expectedTitle, expectedMessage) {
                expect(view.$('.video-detail-status').text().trim()).toEqual('Upload failed');
                expect(view.$('.more-details-action').contents().get(0).nodeValue.trim()).toEqual('Read More');
                expect(view.$('.more-details-action .sr').text().trim()).toEqual('details about the failure');
                view.$('a.more-details-action').click();
                expect($('#prompt-warning-title').text().trim()).toEqual(expectedTitle);
                expect($('#prompt-warning-description').text().trim()).toEqual(expectedMessage);
            };

            getStatusUpdateRequest = function() {
                var sentRequests = getSentRequests();
                return sentRequests.filter(function(request) {
                    return request.method === 'POST' && _.has(
                        JSON.parse(request.params)[0], 'status'
                    );
                })[0];
            };

            verifyStatusUpdateRequest = function(videoId, status, message, expectedRequest) {
                var request = expectedRequest || getStatusUpdateRequest(),
                    expectedData = JSON.stringify({
                        edxVideoId: videoId,
                        status: status,
                        message: message
                    });
                expect(request.method).toEqual('POST');
                expect(request.url).toEqual(POST_URL);
                if (_.has(request, 'requestBody')) {
                    expect(_.isMatch(request.requestBody, expectedData)).toBeTruthy();
                } else {
                    expect(_.isMatch(request.params, expectedData)).toBeTruthy();
                }
            };

            verifyUploadPostRequest = function(requestParams) {
                // get latest requestParams.length requests
                var postRequests = getSentRequests().slice(-requestParams.length);
                _.each(postRequests, function(postRequest, index) {
                    expect(postRequest.method).toEqual('POST');
                    expect(postRequest.url).toEqual(POST_URL);
                    expect(postRequest.params).toEqual(requestParams[index]);
                });
            };

            verifyA11YMessage = function(message) {
                expect($('#reader-feedback').text().trim()).toEqual(message);
            };

            sendUploadPostResponse = function(request, fileNames, url) {
                request.respondWith({
                    status: 200,
                    responseText: JSON.stringify({
                        files: _.map(
                            fileNames,
                            function(fileName) {
                                return {
                                    edx_video_id: VIDEO_ID,
                                    file_name: fileName,
                                    upload_url: url || makeUploadUrl(fileName)
                                };
                            }
                        )
                    })
                });
            };

            describe('errors', function() {
                it('should show error notification for status update request in case of server error', function() {
                    this.view.sendStatusUpdate([
                        {
                            edxVideoId: '101',
                            status: 'upload_completed',
                            message: 'Uploaded completed'
                        }
                    ]);
                    getStatusUpdateRequest().respondWith(
                        {
                            status: 500,
                            responseText: JSON.stringify({
                                error: '500 server errror'
                            })
                        }
                    );
                    expect($('#notification-error-title').text().trim()).toEqual(
                        "Studio's having trouble saving your work"
                    );
                    expect($('#notification-error-description').text().trim()).toEqual('500 server errror');
                });

                it('should correctly parse and show S3 error response xml', function() {
                    var fileInfo = {name: 'video.mp4', size: 10000},
                        videos = {
                            files: [
                                fileInfo
                            ]
                        },
                        S3Url = 'http://s3.aws.com/upload/videos/' + fileInfo.name,
                        requests;

                    // this is required so that we can use AjaxHelpers ajax mock utils instead of jasmine mock-ajax.js
                    jasmine.Ajax.uninstall();

                    requests = AjaxHelpers.requests(this);

                    this.view.$uploadForm.fileupload('add', videos);
                    AjaxHelpers.respond(requests, {
                        status: 200,
                        body: {
                            files: [{
                                edx_video_id: VIDEO_ID,
                                file_name: fileInfo.name,
                                upload_url: S3Url
                            }]
                        }
                    });
                    expect(requests.length).toEqual(2);
                    AjaxHelpers.respond(
                        requests,
                        {
                            statusCode: 403,
                            contentType: 'application/xml',
                            body: '<Error><Message>Invalid access key.</Message></Error>'
                        }
                    );
                    verifyUploadViewInfo(
                        this.view.itemViews[0],
                        'Your file could not be uploaded',
                        'Invalid access key.'
                    );
                    verifyStatusUpdateRequest(
                        VIDEO_ID,
                        UPLOAD_STATUS.s3Fail,
                        'Invalid access key.',
                        AjaxHelpers.currentRequest(requests)
                    );
                    verifyA11YMessage(
                        StringUtils.interpolate('Upload failed for video {fileName}', {fileName: fileInfo.name})
                    );

                    // this is required otherwise mock-ajax will throw an exception when it tries to uninstall Ajax in
                    // outer afterEach
                    jasmine.Ajax.install();
                });
            });

            describe('upload cancelled', function() {
                it('should send correct status update request', function() {
                    var fileInfo = {name: 'video.mp4'},
                        videos = {
                            files: [
                                fileInfo
                            ]
                        },
                        sentRequests,
                        uploadCancelledRequest;

                    this.view.$uploadForm.fileupload('add', videos);
                    sendUploadPostResponse(getSentRequests()[0], [fileInfo.name]);
                    sentRequests = getSentRequests();

                    // no upload cancel request should be sent because `uploading` attribute is not set on model
                    this.view.onUnload();
                    expect(getSentRequests().length).toEqual(sentRequests.length);

                    // set `uploading` attribute on each model
                    this.view.collection.each(function(model) {
                        model.set('uploading', true);
                    });

                    // upload_cancelled request should be sent
                    this.view.onUnload();
                    uploadCancelledRequest = jasmine.Ajax.requests.mostRecent();
                    expect(uploadCancelledRequest.params).toEqual(
                        JSON.stringify(
                            [{
                                edxVideoId: VIDEO_ID,
                                status: 'upload_cancelled',
                                message: 'User cancelled video upload'
                            }]
                        )
                    );
                });
            });

            describe('file formats', function() {
                it('should not fail upload for supported file formats', function() {
                    var supportedFiles = {
                            files: [
                                {name: 'test-1.mp4'},
                                {name: 'test-1.mov'}
                            ]
                        },
                        requestParams = _.map(supportedFiles.files, function(file) {
                            return JSON.stringify({files: [{file_name: file.name}]});
                        });
                    this.view.$uploadForm.fileupload('add', supportedFiles);
                    verifyUploadPostRequest(requestParams);
                });
                it('should fail upload for unspported file formats', function() {
                    var files = [
                            {name: 'test-3.txt', size: 0},
                            {name: 'test-4.png', size: 0}
                        ],
                        unSupportedFiles = {
                            files: files
                        },
                        self = this;

                    this.view.$uploadForm.fileupload('add', unSupportedFiles);
                    _.each(this.view.itemViews, function(uploadView, index) {
                        verifyUploadViewInfo(
                            uploadView,
                            'Your file could not be uploaded',
                            StringUtils.interpolate(
                                '{fileName} is not in a supported file format. Supported file formats are {supportedFormats}.',  // eslint-disable-line max-len
                                {fileName: files[index].name, supportedFormats: self.videoSupportedFileFormats.join(' and ')}  // eslint-disable-line max-len
                            )
                        );
                    });
                });
            });

            describe('Upload file', function() {
                _.each(
                    [
                        {desc: 'larger than', additionalBytes: 1},
                        {desc: 'equal to', additionalBytes: 0},
                        {desc: 'smaller than', additionalBytes: - 1}
                    ],
                    function(caseInfo) {
                        it(caseInfo.desc + 'max file size', function() {
                            var maxFileSizeInBytes = this.view.getMaxFileSizeInBytes(),
                                fileSize = maxFileSizeInBytes + caseInfo.additionalBytes,
                                fileToUpload = {
                                    files: [
                                        {name: 'file.mp4', size: fileSize}
                                    ]
                                },
                                requestParams = _.map(fileToUpload.files, function(file) {
                                    return JSON.stringify({files: [{file_name: file.name}]});
                                }),
                                uploadView;
                            this.view.$uploadForm.fileupload('add', fileToUpload);
                            if (fileSize > maxFileSizeInBytes) {
                                uploadView = this.view.itemViews[0];
                                verifyUploadViewInfo(
                                    uploadView,
                                    'Your file could not be uploaded',
                                    'file.mp4 exceeds maximum size of ' + this.videoUploadMaxFileSizeInGB + ' GB.'
                                );
                                verifyA11YMessage(
                                    StringUtils.interpolate(
                                        'Upload failed for video {fileName}', {fileName: 'file.mp4'}
                                    )
                                );
                            } else {
                                verifyUploadPostRequest(requestParams);
                                sendUploadPostResponse(
                                    getSentRequests()[0],
                                    [fileToUpload.files[0].name]
                                );
                                getSentRequests()[1].respondWith(
                                    {status: 200}
                                );
                                verifyStatusUpdateRequest(
                                    VIDEO_ID,
                                    UPLOAD_STATUS.success,
                                    'Uploaded completed'
                                );
                                verifyA11YMessage(
                                    StringUtils.interpolate(
                                        'Upload completed for video {fileName}', {fileName: fileToUpload.files[0].name}
                                    )
                                );
                            }
                        });
                    }
                );
            });

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
                                if (arguments.length === 2 && propName === 'files') {
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
                            var request,
                                self = this;
                            expect(jasmine.Ajax.requests.count()).toEqual(caseInfo.numFiles);
                            _.each(_.range(caseInfo.numFiles), function(index) {
                                request = jasmine.Ajax.requests.at(index);
                                expect(request.url).toEqual(self.postUrl);
                                expect(request.method).toEqual('POST');
                                expect(request.requestHeaders['Content-Type']).toEqual('application/json');
                                expect(request.requestHeaders.Accept).toContain('application/json');
                                expect(JSON.parse(request.params)).toEqual({
                                    files: [{file_name: fileNames[index]}]
                                });
                            });
                        });

                        describe('and successful server response', function() {
                            beforeEach(function() {
                                jasmine.Ajax.requests.reset();
                                sendUploadPostResponse(this.request, fileNames);
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

                            _.each([true, false],
                                function(isViewRefresh) {
                                    var refreshDescription = isViewRefresh ? ' (refreshed)' : ' (not refreshed)';
                                    var subCases = [
                                        {
                                            desc: 'completion' + refreshDescription,
                                            responseStatus: 204,
                                            statusText: ActiveVideoUpload.STATUS_COMPLETED,
                                            progressValue: 1,
                                            presentClass: 'success',
                                            absentClass: 'error',
                                            isViewRefresh: isViewRefresh
                                        },
                                        {
                                            desc: 'failure' + refreshDescription,
                                            responseStatus: 500,
                                            statusText: ActiveVideoUpload.STATUS_FAILED,
                                            progressValue: 0,
                                            presentClass: 'error',
                                            absentClass: 'success',
                                            isViewRefresh: isViewRefresh
                                        }
                                    ];

                                    _.each(subCases,
                                        function(subCaseInfo) {
                                            describe('and upload ' + subCaseInfo.desc, function() {
                                                var refreshSpy = null;

                                                beforeEach(function() {
                                                    refreshSpy = subCaseInfo.isViewRefresh ? jasmine.createSpy() : null;
                                                    this.view.onFileUploadDone = refreshSpy;
                                                    getSentRequests()[0].respondWith(
                                                        {status: subCaseInfo.responseStatus}
                                                    );
                                                    // after successful upload, status update request is sent to server
                                                    // we re-render views after success response is received from server
                                                    if (subCaseInfo.statusText === ActiveVideoUpload.STATUS_COMPLETED) {
                                                        getStatusUpdateRequest().respondWith(
                                                            {status: 200}
                                                        );
                                                    }
                                                });

                                                it('should update status and progress', function() {
                                                    var $uploadElem = this.view.$('.active-video-upload:first');
                                                    if (subCaseInfo.isViewRefresh &&
                                                        subCaseInfo.responseStatus === 204) {
                                                        expect(refreshSpy).toHaveBeenCalled();
                                                        if ($uploadElem.length > 0) {
                                                            expect(
                                                                $.trim($uploadElem.find('.video-detail-status').text())
                                                            ).not.toEqual(ActiveVideoUpload.STATUS_COMPLETED);
                                                            expect(
                                                                $uploadElem.find('.video-detail-progress').val()
                                                            ).not.toEqual(1);
                                                            expect($uploadElem).not.toHaveClass('success');
                                                        }
                                                    } else {
                                                        expect($uploadElem.length).toEqual(1);
                                                        expect(
                                                            $.trim($uploadElem.find('.video-detail-status').text())
                                                        ).toEqual(subCaseInfo.statusText);
                                                        expect(
                                                            $uploadElem.find('.video-detail-progress').val()
                                                        ).toEqual(subCaseInfo.progressValue);
                                                        expect($uploadElem).toHaveClass(subCaseInfo.presentClass);
                                                        expect($uploadElem).not.toHaveClass(subCaseInfo.absentClass);
                                                    }
                                                });

                                                if (caseInfo.numFiles > concurrentUploadLimit) {
                                                    it('should start a new upload', function() {
                                                        var $uploadElem = $(this.$uploadElems[concurrentUploadLimit]);

                                                        // we try to upload 3 files. 2 files(2 requests) will start
                                                        // uploading immediately and third one will be queued, after
                                                        // an upload is completed, queued file(3rd request) will start
                                                        // uploading, 4th request will be sent to server to update
                                                        // status for completed upload
                                                        expect(getSentRequests().length).toEqual(
                                                            concurrentUploadLimit + 1 + 1
                                                        );
                                                        expect(
                                                            $.trim($uploadElem.find('.video-detail-status').text())
                                                        ).toEqual(ActiveVideoUpload.STATUS_UPLOADING);
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
                                }
                            );
                        });
                    });
                }
            );
        });
    }
);
