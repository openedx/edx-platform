define(
    [
        'jquery', 'underscore', 'backbone',
        'js/views/video/transcripts/utils', 'js/views/video/transcripts/file_uploader',
        'xmodule', 'jquery.form'
    ],
function($, _, Backbone, Utils, FileUploader) {
    'use strict';

    describe('Transcripts.FileUploader', function() {
        var videoListEntryTemplate = readFixtures(
                'video/transcripts/metadata-videolist-entry.underscore'
            ),
            fileUploadTemplate = readFixtures(
                'video/transcripts/file-upload.underscore'
            ),
            view;

        beforeEach(function() {
            setFixtures(
                $('<div>', {id: 'metadata-videolist-entry'})
                    .html(videoListEntryTemplate)
            );
            appendSetFixtures(
                $('<script>',
                    {
                        id: 'file-upload',
                        type: 'text/template'
                    }
                ).text(fileUploadTemplate)
            );

            var messenger = jasmine.createSpyObj(
                    'MessageManager',
                    ['render', 'showError', 'hideError']
                ),
                $container = $('.transcripts-status');

            $container
                .append('<div class="transcripts-file-uploader" />')
                .append('<a class="setting-upload" href="#">Upload</a>');

            spyOn(FileUploader.prototype, 'render').and.callThrough();

            view = new FileUploader({
                el: $container,
                messenger: messenger,
                component_locator: 'component_locator'
            });
        });

        it('Initialize', function() {
            expect(view.file).toBe(false);
            expect(FileUploader.prototype.render).toHaveBeenCalled();
        });

        describe('Render', function() {
            beforeEach(function() {
                spyOn(_, 'template').and.callThrough();
            });

            it('Template doesn\'t exist', function() {
                spyOn(console, 'error');
                view.uploadTpl = '';

                expect(view.render).not.toThrow();
                expect(console.error).toHaveBeenCalled();
                expect(_.template).not.toHaveBeenCalled();
            });

            it('Container where template will be inserted doesn\'t exist',
                function() {
                    $('.transcripts-file-uploader').remove();

                    expect(view.render).not.toThrow();
                    expect(_.template).not.toHaveBeenCalled();
                }
            );

            it('All works okay if all data is okay', function() {
                var elList = ['$form', '$input', '$progress'],
                    validFileExtensions = ['srt', 'sjson'],
                    result = $.map(validFileExtensions, function(item, index) {
                        return '.' + item;
                    }).join(', ');

                view.validFileExtensions = validFileExtensions;
                expect(view.render).not.toThrow();
                expect(_.template).toHaveBeenCalled();
                $.each(elList, function(index, el) {
                    expect(view[el].length).not.toBe(0);
                });
                expect(view.$input.attr('accept')).toBe(result);
            });
        });

        describe('Upload', function() {
            it('File is not chosen', function() {
                spyOn($.fn, 'ajaxSubmit');
                view.upload();

                expect(view.$form.ajaxSubmit).not.toHaveBeenCalled();
            });

            it('File is chosen', function() {
                spyOn($.fn, 'ajaxSubmit');

                view.file = {};
                view.upload();

                expect(view.$form.ajaxSubmit).toHaveBeenCalled();
            });
        });

        it('clickHandler', function() {
            spyOn($.fn, 'trigger');

            $('.setting-upload').click();

            expect($('.setting-upload').trigger).toHaveBeenCalledWith('click');
            expect(view.$input).toHaveValue('');
        });

        describe('changeHadler', function() {
            beforeEach(function() {
                spyOn(view, 'upload');
            });

            it('Valid File Type - error should be hided', function() {
                spyOn(view, 'checkExtValidity').and.returnValue(true);

                view.$input.change();

                expect(view.checkExtValidity).toHaveBeenCalled();
                expect(view.upload).toHaveBeenCalled();
                expect(view.options.messenger.hideError).toHaveBeenCalled();
            });

            it('Invalid File Type - error should be shown', function() {
                spyOn(view, 'checkExtValidity').and.returnValue(false);

                view.$input.change();

                expect(view.checkExtValidity).toHaveBeenCalled();
                expect(view.upload).not.toHaveBeenCalled();
                expect(view.options.messenger.showError).toHaveBeenCalled();
            });
        });

        describe('checkExtValidity', function() {
            var data = {
                Correct: {
                    name: 'file_name.srt',
                    isValid: true
                },
                Incorrect: {
                    name: 'file_name.mp4',
                    isValid: false
                }
            };

            $.each(data, function(fileType, fileInfo) {
                it(fileType + ' file type', function() {
                    var result = view.checkExtValidity(fileInfo);

                    expect(result).toBe(fileInfo.isValid);
                });
            });
        });

        it('xhrResetProgressBar', function() {
            view.xhrResetProgressBar();
            expect(view.$progress.width()).toBe(0);
            expect(view.$progress.html()).toBe('0%');
            expect(view.$progress).not.toHaveClass('is-invisible');
        });

        it('xhrProgressHandler', function() {
            var percent = 26;

            spyOn($.fn, 'width').and.callThrough();

            view.xhrProgressHandler(null, null, null, percent);
            expect(view.$progress.width).toHaveBeenCalledWith(percent + '%');
            expect(view.$progress.html()).toBe(percent + '%');
        });

        describe('xhrCompleteHandler', function() {
            it('Ajax Success', function() {
                var xhr = {
                    status: 200,
                    responseText: JSON.stringify({
                        status: 'Success',
                        edx_video_id: 'test_video_id'
                    })
                };
                spyOn(Backbone, 'trigger');
                view.xhrCompleteHandler(xhr);

                expect(view.$progress).toHaveClass('is-invisible');
                expect(view.options.messenger.render.calls.mostRecent().args[0])
                    .toEqual('uploaded');
                expect(Backbone.trigger)
                    .toHaveBeenCalledWith('transcripts:basicTabUpdateEdxVideoId', 'test_video_id');
            });

            var assertAjaxError = function(xhr) {
                spyOn(Utils.Storage, 'set');
                view.xhrCompleteHandler(xhr);

                expect(view.options.messenger.showError).toHaveBeenCalled();
                expect(view.$progress).toHaveClass('is-invisible');
                expect(view.options.messenger.render)
                    .not
                    .toHaveBeenCalled();
                expect(Utils.Storage.set)
                    .not
                    .toHaveBeenCalledWith('sub', 'test');
            };

            it('Ajax transport Error', function() {
                var xhr = {
                    status: 400,
                    responseText: JSON.stringify({})
                };

                assertAjaxError(xhr);
            });
        });
    });
});
