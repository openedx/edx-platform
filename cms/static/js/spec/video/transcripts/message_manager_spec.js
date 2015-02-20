define(
    [
        "jquery", "underscore",
        "js/views/video/transcripts/utils", "js/views/video/transcripts/message_manager",
        "js/views/video/transcripts/file_uploader", "sinon", "jasmine-jquery",
        "xmodule"
    ],
function ($, _, Utils, MessageManager, FileUploader, sinon) {

    // TODO: fix TNL-559 Intermittent failures of Transcript FileUploader JS tests
    xdescribe('Transcripts.MessageManager', function () {
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

        beforeEach(function () {
            var videoList, $container;

            fileUploader = FileUploader.prototype;

            setFixtures(
                $("<div>", {id: "metadata-videolist-entry"})
                    .html(videoListEntryTemplate)
            );
            appendSetFixtures(
                $("<script>",
                    {
                        id: "transcripts-found",
                        type: "text/template"
                    }
                ).text(foundTemplate)
            );

            videoList = jasmine.createSpyObj(
                'MetadataView.VideoList',
                ['getVideoObjectsList']
            );
            $container = $('#metadata-videolist-entry');

            spyOn(fileUploader, 'initialize');
            spyOn(console, 'error');
            spyOn(Utils.Storage, 'set');

            view = new MessageManager({
                el: $container,
                parent: videoList,
                component_locator: 'component_locator'
            });
        });

        it('Initialize', function () {
            expect(fileUploader.initialize).toHaveBeenCalledWith({
                el: view.$el,
                messenger: view,
                component_locator: view.component_locator,
                videoListObject: view.options.parent
            });
        });

        // Disabled 2/6/14 after intermittent failure in master
        xdescribe('Render', function () {

            beforeEach(function () {
                spyOn(_,'template').andCallThrough();
                spyOn(fileUploader, 'render');
            });

            it('Template doesn\'t exist', function () {
                view.render('incorrect_template_name');

                expect(console.error).toHaveBeenCalled();
                expect(_.template).not.toHaveBeenCalled();
                expect(view.$el.find('.transcripts-status'))
                    .toHaveClass('is-invisible');
                expect(fileUploader.render).not.toHaveBeenCalled();
            });

            it('All works okay if correct data is passed', function () {
                view.render('found');

                expect(console.error).not.toHaveBeenCalled();
                expect(_.template).toHaveBeenCalled();
                expect(view.$el).not.toHaveClass('is-invisible');
                expect(fileUploader.render).toHaveBeenCalled();
            });
        });

        describe('showError', function () {
            var errorMessage ='error',
                $error, $buttons;

            beforeEach(function () {
                view.render('found');
                spyOn(view, 'hideError');
                spyOn($.fn, 'html').andCallThrough();
                $error = view.$el.find('.transcripts-error-message');
                $buttons = view.$el.find('.wrapper-transcripts-buttons');
            });

            it('Error message is not passed', function () {
                view.showError(null);

                expect(view.hideError).not.toHaveBeenCalled();
                expect($error.html).not.toHaveBeenCalled();
                expect($error).toHaveClass('is-invisible');
                expect($buttons).not.toHaveClass('is-invisible');
            });

            it('Show message and buttons', function () {
                view.showError(errorMessage);

                expect(view.hideError).toHaveBeenCalled();
                expect($error.html).toHaveBeenCalled();
                expect($error).not.toHaveClass('is-invisible');
                expect($buttons).not.toHaveClass('is-invisible');
            });

            it('Show message and hide buttons', function () {
                view.showError(errorMessage, true);

                expect(view.hideError).toHaveBeenCalled();
                expect($error.html).toHaveBeenCalled();
                expect($error).not.toHaveClass('is-invisible');
                expect($buttons).toHaveClass('is-invisible');
            });
        });

        it('hideError', function () {
            view.render('found');

            var $error = view.$el.find('.transcripts-error-message'),
                $buttons = view.$el.find('.wrapper-transcripts-buttons');

            expect($error).toHaveClass('is-invisible');
            expect($buttons).not.toHaveClass('is-invisible');
        });

        $.each(handlers, function(key, value) {
             it(key, function () {
                var eventObj = jasmine.createSpyObj('event', ['preventDefault']);
                spyOn($.fn, 'data').andReturn('video_id');
                spyOn(view, 'processCommand');
                view[key](eventObj);
                expect(view.processCommand.mostRecentCall.args).toEqual(value);
             });
        });

        describe('processCommand', function () {
            var action = 'replace',
                errorMessage = 'errorMessage',
                videoList = void(0),
                extraParamas = 'video_id';

            beforeEach(function () {
                view.render('found');
                spyOn(Utils, 'command').andCallThrough();
                spyOn(view, 'render');
                spyOn(view, 'showError');

                sinonXhr =  sinon.fakeServer.create();
                sinonXhr.autoRespond = true;
            });

            afterEach(function () {
                sinonXhr.restore();
            });

            var assertCommand = function (config, expectFunc) {
                var flag = false,
                    defaults = {
                        action: 'replace',
                        errorMessage: 'errorMessage',
                        extraParamas: void(0)
                    };
                    args = $.extend({}, defaults, config);

                runs(function() {
                    view
                        .processCommand(
                            args.action,
                            args.errorMessage,
                            args.extraParamas
                        )
                        .always(function () { flag = true; });
                });

                waitsFor(function() {
                    return flag;
                }, "Ajax Timeout", 750);


                runs(expectFunc);
            };

            it('Invoke without extraParamas', function () {

                sinonXhr.respondWith([
                    200,
                    { "Content-Type": "application/json"},
                    JSON.stringify({
                      status: 'Success',
                      subs: 'video_id'
                    })
                ]);

                assertCommand(
                    { },
                    function() {
                        expect(Utils.command).toHaveBeenCalledWith(
                            action,
                            view.component_locator,
                            videoList,
                            void(0)
                        );
                        expect(view.showError).not.toHaveBeenCalled();
                        expect(view.render.mostRecentCall.args[0])
                            .toEqual('found');
                        expect(Utils.Storage.set).toHaveBeenCalled();
                    }
                );
            });

            it('Invoke with extraParamas', function () {

                sinonXhr.respondWith([
                    200,
                    { "Content-Type": "application/json"},
                    JSON.stringify({
                      status: 'Success',
                      subs: 'video_id'
                    })
                ]);

                view.processCommand(action, errorMessage, extraParamas);

                assertCommand(
                    { extraParamas : extraParamas },
                    function () {
                        expect(Utils.command).toHaveBeenCalledWith(
                            action,
                            view.component_locator,
                            videoList,
                            {
                                html5_id: extraParamas
                            }
                        );
                        expect(view.showError).not.toHaveBeenCalled();
                        expect(view.render.mostRecentCall.args[0])
                            .toEqual('found');
                        expect(Utils.Storage.set).toHaveBeenCalled();
                    }
                );
            });

            it('Fail', function () {

                sinonXhr.respondWith([400, {}, '']);

                assertCommand(
                    { },
                    function () {
                        expect(Utils.command).toHaveBeenCalledWith(
                            action,
                            view.component_locator,
                            videoList,
                            void(0)
                        );
                        expect(view.showError).toHaveBeenCalled();
                        expect(view.render).not.toHaveBeenCalled();
                        expect(Utils.Storage.set).not.toHaveBeenCalled();
                    }
                );
            });
        });

    });
});
