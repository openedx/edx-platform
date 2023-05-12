// eslint-disable-next-line no-undef
define(
    [
        'jquery', 'underscore', 'backbone',
        'js/views/video/transcripts/utils', 'js/views/video/transcripts/message_manager',
        'js/views/video/transcripts/file_uploader', 'sinon',
        'xmodule'
    ],
    function($, _, Backbone, Utils, MessageManager, FileUploader, sinon) {
        'use strict';

        describe('Transcripts.MessageManager', function() {
            // eslint-disable-next-line no-var
            var videoListEntryTemplate = readFixtures(
                    'video/transcripts/metadata-videolist-entry.underscore'
                ),
                foundTemplate = readFixtures(
                    'video/transcripts/messages/transcripts-found.underscore'
                ),
                handlers = {
                    importHandler: ['replace', 'Error: Import failed.'],
                    replaceHandler: ['replace', 'Error: Replacing failed.'],
                    chooseHandler: ['choose', 'Error: Choosing failed.', 'video_id']
                },
                view, fileUploader, sinonXhr;

            beforeEach(function() {
                // eslint-disable-next-line no-var
                var videoList, $container;

                fileUploader = FileUploader.prototype;

                setFixtures(
                    $('<div>', {id: 'metadata-videolist-entry'})
                        .html(videoListEntryTemplate)
                );
                appendSetFixtures(
                    $('<script>',
                        {
                            id: 'transcripts-found',
                            type: 'text/template'
                        }
                    ).text(foundTemplate)
                );

                // eslint-disable-next-line no-undef
                videoList = jasmine.createSpyObj(
                    'MetadataView.VideoList',
                    ['getVideoObjectsList']
                );
                $container = $('#metadata-videolist-entry');

                // eslint-disable-next-line no-undef
                spyOn(fileUploader, 'initialize').and.callThrough();
                // eslint-disable-next-line no-undef
                spyOn(console, 'error');
                // eslint-disable-next-line no-undef
                spyOn(Utils.Storage, 'set');

                view = new MessageManager({
                    el: $container,
                    parent: videoList,
                    component_locator: 'component_locator'
                });
            });

            it('Initialize', function() {
                expect(fileUploader.initialize).toHaveBeenCalledWith({
                    el: view.$el,
                    messenger: view,
                    component_locator: view.component_locator
                });
            });

            describe('Render', function() {
                beforeEach(function() {
                    // eslint-disable-next-line no-undef
                    spyOn(_, 'template').and.callThrough();
                    // eslint-disable-next-line no-undef
                    spyOn(view.fileUploader, 'render');
                });

                it('Template doesn\'t exist', function() {
                    view.render('incorrect_template_name');

                    // eslint-disable-next-line no-console
                    expect(console.error).toHaveBeenCalled();
                    expect(_.template).not.toHaveBeenCalled();
                    expect(view.$el.find('.transcripts-status'))
                        .toHaveClass('is-invisible');
                    expect(view.fileUploader.render).not.toHaveBeenCalled();
                });

                it('All works okay if correct data is passed', function() {
                    view.render('found');

                    // eslint-disable-next-line no-console
                    expect(console.error).not.toHaveBeenCalled();
                    expect(_.template).toHaveBeenCalled();
                    expect(view.$el).not.toHaveClass('is-invisible');
                    expect(view.fileUploader.render).toHaveBeenCalled();
                });
            });

            describe('showError', function() {
                // eslint-disable-next-line no-var
                var errorMessage = 'error',
                    $error, $buttons;

                beforeEach(function() {
                    view.render('found');
                    // eslint-disable-next-line no-undef
                    spyOn(view, 'hideError');
                    // eslint-disable-next-line no-undef
                    spyOn($.fn, 'html').and.callThrough();
                    $error = view.$el.find('.transcripts-error-message');
                    $buttons = view.$el.find('.wrapper-transcripts-buttons');
                });

                it('Error message is not passed', function() {
                    view.showError(null);

                    expect(view.hideError).not.toHaveBeenCalled();
                    expect($error.html).not.toHaveBeenCalled();
                    expect($error).toHaveClass('is-invisible');
                    expect($buttons).not.toHaveClass('is-invisible');
                });

                it('Show message and buttons', function() {
                    view.showError(errorMessage);

                    expect(view.hideError).toHaveBeenCalled();
                    expect($error.html).toHaveBeenCalled();
                    expect($error).not.toHaveClass('is-invisible');
                    expect($buttons).not.toHaveClass('is-invisible');
                });

                it('Show message and hide buttons', function() {
                    view.showError(errorMessage, true);

                    expect(view.hideError).toHaveBeenCalled();
                    expect($error.html).toHaveBeenCalled();
                    expect($error).not.toHaveClass('is-invisible');
                    expect($buttons).toHaveClass('is-invisible');
                });
            });

            it('hideError', function() {
                view.render('found');

                // eslint-disable-next-line no-var
                var $error = view.$el.find('.transcripts-error-message'),
                    $buttons = view.$el.find('.wrapper-transcripts-buttons');

                expect($error).toHaveClass('is-invisible');
                expect($buttons).not.toHaveClass('is-invisible');
            });

            $.each(handlers, function(key, value) {
                it(key, function() {
                    /* eslint-disable-next-line no-undef, no-var */
                    var eventObj = jasmine.createSpyObj('event', ['preventDefault']);
                    // eslint-disable-next-line no-undef
                    spyOn($.fn, 'data').and.returnValue('video_id');
                    // eslint-disable-next-line no-undef
                    spyOn(view, 'processCommand');
                    view[key](eventObj);
                    expect(view.processCommand.calls.mostRecent().args).toEqual(value);
                });
            });

            describe('processCommand', function() {
                // eslint-disable-next-line no-var
                var action = 'replace',
                    errorMessage = 'errorMessage',
                    // eslint-disable-next-line no-void
                    videoList = void 0,
                    extraParamas = 'video_id';

                beforeEach(function() {
                    view.render('found');
                    // eslint-disable-next-line no-undef
                    spyOn(Utils, 'command').and.callThrough();
                    // eslint-disable-next-line no-undef
                    spyOn(view, 'render');
                    // eslint-disable-next-line no-undef
                    spyOn(view, 'showError');

                    sinonXhr = sinon.fakeServer.create();
                    sinonXhr.autoRespond = true;
                });

                afterEach(function() {
                    sinonXhr.restore();
                });

                // eslint-disable-next-line no-var
                var assertCommand = function(config) {
                    // eslint-disable-next-line no-var
                    var defaults = {
                        action: 'replace',
                        errorMessage: 'errorMessage',
                        // eslint-disable-next-line no-void
                        extraParamas: void 0
                    };
                    // eslint-disable-next-line no-var
                    var args = $.extend({}, defaults, config);

                    return view
                        .processCommand(args.action, args.errorMessage, args.extraParamas);
                };

                it('Invoke without extraParamas', function(done) {
                    // eslint-disable-next-line no-undef
                    spyOn(Backbone, 'trigger');

                    sinonXhr.respondWith([
                        200,
                        {'Content-Type': 'application/json'},
                        JSON.stringify({
                            status: 'Success',
                            edx_video_id: 'video_id'
                        })
                    ]);

                    assertCommand({})
                        .then(function() {
                            expect(Utils.command).toHaveBeenCalledWith(
                                action,
                                view.component_locator,
                                videoList,
                                // eslint-disable-next-line no-void
                                void 0
                            );
                            expect(view.showError).not.toHaveBeenCalled();
                            expect(view.render.calls.mostRecent().args[0]).toEqual('found');
                            expect(Backbone.trigger)
                                .toHaveBeenCalledWith('transcripts:basicTabUpdateEdxVideoId', 'video_id');
                        })
                        .always(done);
                });

                it('Invoke with extraParamas', function(done) {
                    // eslint-disable-next-line no-undef
                    spyOn(Backbone, 'trigger');

                    sinonXhr.respondWith([
                        200,
                        {'Content-Type': 'application/json'},
                        JSON.stringify({
                            status: 'Success',
                            edx_video_id: 'video_id'
                        })
                    ]);

                    view.processCommand(action, errorMessage, extraParamas);

                    assertCommand({extraParamas: extraParamas})
                        .then(function() {
                            expect(Utils.command).toHaveBeenCalledWith(
                                action,
                                view.component_locator,
                                videoList,
                                {
                                    html5_id: extraParamas
                                }
                            );
                            expect(view.showError).not.toHaveBeenCalled();
                            expect(view.render.calls.mostRecent().args[0]).toEqual('found');
                            expect(Backbone.trigger)
                                .toHaveBeenCalledWith('transcripts:basicTabUpdateEdxVideoId', 'video_id');
                        })
                        .always(done);
                });

                it('Fail', function(done) {
                    sinonXhr.respondWith([400, {}, '']);
                    assertCommand({})
                        .then(function() {
                            expect(Utils.command).toHaveBeenCalledWith(
                                action,
                                view.component_locator,
                                videoList,
                                // eslint-disable-next-line no-void
                                void 0
                            );
                            expect(view.showError).toHaveBeenCalled();
                            expect(view.render).not.toHaveBeenCalled();
                            expect(Utils.Storage.set).not.toHaveBeenCalled();
                        })
                        .always(done);
                });
            });
        });
    });
