define(
    [
        'jquery', 'underscore', 'backbone',
        'edx-ui-toolkit/js/utils/spec-helpers/ajax-helpers',
        'js/views/video/transcripts/utils',
        'js/views/video/transcripts/editor',
        'js/views/video/transcripts/metadata_videolist', 'js/models/metadata',
        'js/views/abstract_editor',
        'js/views/video/transcripts/message_manager',
        'xmodule'
    ],
    function($, _, Backbone, AjaxHelpers, Utils, Editor, VideoList, MetadataModel, AbstractEditor, MessageManager) {
        'use strict';
        describe('CMS.Views.Metadata.VideoList', function() {
            var videoListEntryTemplate = readFixtures(
                    'video/transcripts/metadata-videolist-entry.underscore'
                ),
                abstractEditor = AbstractEditor.prototype,
                component_locator = 'component_locator',
                videoList = [
                    {
                        mode: 'youtube',
                        type: 'youtube',
                        video: '12345678901'
                    },
                    {
                        mode: 'html5',
                        type: 'mp4',
                        video: 'video'
                    },
                    {
                        mode: 'html5',
                        type: 'webm',
                        video: 'video'
                    }
                ],
                modelStub = {
                    default_value: ['a thing', 'another thing'],
                    display_name: 'Video URL',
                    explicitly_set: true,
                    field_name: 'video_url',
                    help: 'A list of things.',
                    options: [],
                    type: MetadataModel.VIDEO_LIST_TYPE,
                    value: [
                        'http://youtu.be/12345678901',
                        'video.mp4',
                        'video.webm'
                    ]
                },
                videoIDStub = {
                    default_value: 'test default value',
                    display_name: 'Video ID',
                    explicitly_set: true,
                    field_name: 'edx_video_id',
                    help: 'Specifies the video ID.',
                    options: [],
                    type: 'VideoID',
                    value: 'advanced tab video id'
                },
                response = JSON.stringify({
                    command: 'found',
                    status: 'Success',
                    subs: 'video_id'
                }),
                waitForEvent,
                createVideoListView;


            var createMockAjaxServer = function() {
                var mockServer = AjaxHelpers.server(
                    [
                        200,
                        {'Content-Type': 'application/json'},
                        response
                    ]
                );
                mockServer.autoRespond = true;
                return mockServer;
            };

            beforeEach(function() {
                var tpl = sandbox({  // eslint-disable-line no-undef
                    class: 'component',
                    'data-locator': component_locator
                });

                setFixtures(tpl);

                appendSetFixtures(
                    $('<script>',
                        {
                            id: 'metadata-videolist-entry',
                            type: 'text/template'
                        }
                    ).text(videoListEntryTemplate)
                );

                // create mock server
                this.mockServer = createMockAjaxServer();

                spyOn($.fn, 'on').and.callThrough();
                spyOn(Backbone, 'trigger').and.callThrough();
                spyOn(Utils, 'command').and.callThrough();
                spyOn(abstractEditor, 'initialize').and.callThrough();
                spyOn(abstractEditor, 'render').and.callThrough();
                spyOn(console, 'error');

                spyOn(MessageManager.prototype, 'initialize').and.callThrough();
                spyOn(MessageManager.prototype, 'render').and.callThrough();
                spyOn(MessageManager.prototype, 'showError').and.callThrough();
                spyOn(MessageManager.prototype, 'hideError').and.callThrough();

                jasmine.addMatchers({
                    assertValueInView: function() {
                        return {
                            compare: function(actual, expected) {
                                var actualValue = actual.getValueFromEditor(),
                                    passed = _.isEqual(actualValue, expected);

                                return {
                                    pass: passed
                                };
                            }
                        };
                    },
                    assertCanUpdateView: function() {
                        return {
                            compare: function(actual, expected) {
                                var actualValue,
                                    passed;

                                actual.setValueInEditor(expected);
                                actualValue = actual.getValueFromEditor();
                                passed = _.isEqual(actualValue, expected);

                                return {
                                    pass: passed
                                };
                            }
                        };
                    },
                    assertIsCorrectVideoList: function() {
                        return {
                            compare: function(actual, expected) {
                                var actualValue = actual.getVideoObjectsList(),
                                    passed = _.isEqual(actualValue, expected);

                                return {
                                    pass: passed
                                };
                            }
                        };
                    }
                });
            });

            afterEach(function() {
            // restore mock server
                this.mockServer.restore();
            });

            waitForEvent = function() {
                var triggerCallArgs;
                return jasmine.waitUntil(function() {
                    triggerCallArgs = Backbone.trigger.calls.mostRecent().args;
                    return Backbone.trigger.calls.count() === 1 &&
                    triggerCallArgs[0] === 'transcripts:basicTabFieldChanged';
                });
            };

            createVideoListView = function(mockServer) {
                var $container, editor, model, videoListView;

                appendSetFixtures(
                    sandbox({  // eslint-disable-line no-undef
                        class: 'wrapper-comp-settings basic_metadata_edit',
                        'data-metadata': JSON.stringify({video_url: modelStub, edx_video_id: videoIDStub})
                    })
                );

                $container = $('.basic_metadata_edit');
                editor = new Editor({
                    el: $container
                });

                spyOn(editor, 'getLocator').and.returnValue(component_locator);

                // reset
                Backbone.trigger.calls.reset();
                mockServer.requests.length = 0;

                model = new MetadataModel(modelStub);
                videoListView = new VideoList({
                    el: $('.component'),
                    model: model,
                    MessageManager: MessageManager
                });

                waitForEvent()
                    .then(function() {
                        return true;
                    });

                return videoListView;
            };

            var waitsForResponse = function(mockServer) {
                return jasmine.waitUntil(function() {
                    var requests = mockServer.requests,
                        len = requests.length;

                    return len && requests[0].readyState === 4;
                });
            };


            it('Initialize', function(done) {
                var view = createVideoListView(this.mockServer),
                    callArgs;
                waitsForResponse(this.mockServer)
                    .then(function() {
                        expect(abstractEditor.initialize).toHaveBeenCalled();
                        expect(MessageManager.prototype.initialize).toHaveBeenCalled();
                        expect(view.component_locator).toBe(component_locator);
                        expect(view.$el).toHandle('input');
                        callArgs = view.$el.on.calls.mostRecent().args;
                        expect(callArgs[0]).toEqual('input');
                        expect(callArgs[1]).toEqual('.videolist-settings-item input');
                    }).always(done);
            });

            describe('Render', function() {
                var assertToHaveBeenRendered = function(expectedVideoList) {
                        var commandCallArgs = Utils.command.calls.mostRecent().args,
                            actualVideoList = commandCallArgs[2].slice(0, expectedVideoList.length);

                        expect(commandCallArgs[0]).toEqual('check');
                        expect(commandCallArgs[1]).toEqual(component_locator);
                        _.each([0, 1, 2], function(index) {
                            expect(_.isEqual(expectedVideoList[index], actualVideoList[index])).toBeTruthy();
                        });

                        expect(abstractEditor.render).toHaveBeenCalled();
                        expect(MessageManager.prototype.render).toHaveBeenCalled();
                    },
                    resetSpies = function(mockServer) {
                        abstractEditor.render.calls.reset();
                        Utils.command.calls.reset();
                        MessageManager.prototype.render.calls.reset();
                        mockServer.requests.length = 0;  // eslint-disable-line no-param-reassign
                    };

                afterEach(function() {
                    Backbone.trigger('xblock:editorModalHidden');
                });

                it('is rendered in correct way', function(done) {
                    var view = createVideoListView(this.mockServer);
                    waitsForResponse(this.mockServer)
                        .then(function() {
                            assertToHaveBeenRendered(videoList);
                        })
                        .always(done);
                });

                it('is rendered with opened extra videos bar', function(done) {
                    var view = createVideoListView(this.mockServer);
                    var videoListLength = [
                            {
                                mode: 'youtube',
                                type: 'youtube',
                                video: '12345678901'
                            },
                            {
                                mode: 'html5',
                                type: 'mp4',
                                video: 'video'
                            }
                        ],
                        videoListHtml5mode = [
                            {
                                mode: 'html5',
                                type: 'mp4',
                                video: 'video'
                            }
                        ];

                    spyOn(VideoList.prototype, 'getVideoObjectsList').and.returnValue(videoListLength);
                    spyOn(VideoList.prototype, 'openExtraVideosBar');

                    resetSpies(this.mockServer);
                    view.render();

                    waitsForResponse(this.mockServer)
                        .then(function() {
                            assertToHaveBeenRendered(videoListLength);
                            view.getVideoObjectsList.and.returnValue(videoListLength);
                            expect(view.openExtraVideosBar).toHaveBeenCalled();
                        })
                        .then(_.bind(function() {
                            resetSpies(this.mockServer);
                            view.openExtraVideosBar.calls.reset();
                            view.getVideoObjectsList.and.returnValue(videoListHtml5mode);
                            view.render();

                            return waitsForResponse(this.mockServer)
                                .then(function() {
                                    assertToHaveBeenRendered(videoListHtml5mode);
                                    expect(view.openExtraVideosBar).toHaveBeenCalled();
                                }).then(done);
                        }, this));
                });

                it('is rendered without opened extra videos bar', function(done) {
                    var view = createVideoListView(this.mockServer),
                        videoList = [
                            {
                                mode: 'youtube',
                                type: 'youtube',
                                video: '12345678901'
                            }
                        ];

                    spyOn(VideoList.prototype, 'getVideoObjectsList').and.returnValue(videoList);
                    spyOn(VideoList.prototype, 'closeExtraVideosBar');

                    resetSpies(this.mockServer);
                    view.render();

                    waitsForResponse(this.mockServer)
                        .then(function() {
                            assertToHaveBeenRendered(videoList);
                            expect(view.closeExtraVideosBar).toHaveBeenCalled();
                        })
                        .always(done);
                });
            });

            describe('isUniqOtherVideos', function() {
                it('Unique data - return true', function(done) {
                    var view = createVideoListView(this.mockServer),
                        data = videoList.concat([{
                            mode: 'html5',
                            type: 'other',
                            video: 'pxxZrg'
                        }]);

                    waitsForResponse(this.mockServer)
                        .then(function() {
                            var result = view.isUniqOtherVideos(data);
                            expect(result).toBe(true);
                        })
                        .always(done);
                });

                it('Not Unique data - return false', function(done) {
                    var view = createVideoListView(this.mockServer),
                        data = [
                            {
                                mode: 'html5',
                                type: 'mp4',
                                video: 'video'
                            },
                            {
                                mode: 'html5',
                                type: 'mp4',
                                video: 'video'
                            },
                            {
                                mode: 'html5',
                                type: 'other',
                                video: 'pxxZrg'
                            },
                            {
                                mode: 'html5',
                                type: 'other',
                                video: 'pxxZrg'
                            },
                            {
                                mode: 'youtube',
                                type: 'youtube',
                                video: '12345678901'
                            }
                        ];

                    waitsForResponse(this.mockServer)
                        .then(function() {
                            var result = view.isUniqOtherVideos(data);
                            expect(result).toBe(false);
                        })
                        .always(done);
                });
            });

            describe('isUniqVideoTypes', function() {
                it('Unique data - return true', function(done) {
                    var view = createVideoListView(this.mockServer),
                        data = videoList;

                    waitsForResponse(this.mockServer)
                        .then(function() {
                            var result = view.isUniqVideoTypes(data);
                            expect(result).toBe(true);
                        })
                        .always(done);
                });

                it('Not Unique data - return false', function(done) {
                    var view = createVideoListView(this.mockServer),
                        data = [
                            {
                                mode: 'html5',
                                type: 'mp4',
                                video: 'video'
                            },
                            {
                                mode: 'html5',
                                type: 'mp4',
                                video: 'video'
                            },
                            {
                                mode: 'html5',
                                type: 'other',
                                video: 'pxxZrg'
                            },
                            {
                                mode: 'youtube',
                                type: 'youtube',
                                video: '12345678901'
                            }
                        ];

                    waitsForResponse(this.mockServer)
                        .then(function() {
                            var result = view.isUniqVideoTypes(data);
                            expect(result).toBe(false);
                        })
                        .always(done);
                });
            });

            describe('checkIsUniqVideoTypes', function() {
                it('Error is shown', function(done) {
                    var view = createVideoListView(this.mockServer),
                        data = [
                            {
                                mode: 'html5',
                                type: 'mp4',
                                video: 'video'
                            },
                            {
                                mode: 'html5',
                                type: 'mp4',
                                video: 'video'
                            },
                            {
                                mode: 'html5',
                                type: 'other',
                                video: 'pxxZrg'
                            },
                            {
                                mode: 'youtube',
                                type: 'youtube',
                                video: '12345678901'
                            }
                        ];

                    waitsForResponse(this.mockServer)
                        .then(function() {
                            var result = view.checkIsUniqVideoTypes(data);

                            expect(MessageManager.prototype.showError).toHaveBeenCalled();
                            expect(result).toBe(false);
                        })
                        .always(done);
                });

                it('All works okay if arguments are not passed', function(done) {
                    var view = createVideoListView(this.mockServer);
                    spyOn(view, 'getVideoObjectsList').and.returnValue(videoList);

                    waitsForResponse(this.mockServer)
                        .then(function() {
                            var result = view.checkIsUniqVideoTypes();

                            expect(view.getVideoObjectsList).toHaveBeenCalled();
                            expect(MessageManager.prototype.showError).not.toHaveBeenCalled();
                            expect(result).toBe(true);
                        })
                        .always(done);
                });
            });

            describe('checkValidity', function() {
                it('Error message is shown', function(done) {
                    var view = createVideoListView(this.mockServer);
                    spyOn(view, 'checkIsUniqVideoTypes').and.returnValue(true);

                    waitsForResponse(this.mockServer)
                        .then(function() {
                            var data = {mode: 'incorrect'},
                                result = view.checkValidity(data, true);

                            expect(MessageManager.prototype.showError).toHaveBeenCalled();
                            expect(view.checkIsUniqVideoTypes).toHaveBeenCalled();
                            expect(result).toBe(false);
                        })
                        .always(done);
                });

                it('Error message is shown when flag is not passed', function(done) {
                    var view = createVideoListView(this.mockServer);
                    spyOn(view, 'checkIsUniqVideoTypes').and.returnValue(true);

                    waitsForResponse(this.mockServer)
                        .then(function() {
                            var data = {mode: 'incorrect'},
                                result = view.checkValidity(data);

                            expect(MessageManager.prototype.showError).not.toHaveBeenCalled();
                            expect(view.checkIsUniqVideoTypes).toHaveBeenCalled();
                            expect(result).toBe(true);
                        }).always(done);
                });

                it('All works okay if correct data is passed', function(done) {
                    var view = createVideoListView(this.mockServer);
                    spyOn(view, 'checkIsUniqVideoTypes').and.returnValue(true);

                    waitsForResponse(this.mockServer)
                        .then(function() {
                            var data = videoList,
                                result = view.checkValidity(data);

                            expect(MessageManager.prototype.showError).not.toHaveBeenCalled();
                            expect(view.checkIsUniqVideoTypes).toHaveBeenCalled();
                            expect(result).toBe(true);
                        })
                        .always(done);
                });
            });

            it('openExtraVideosBar', function(done) {
                var view = createVideoListView(this.mockServer);
                waitsForResponse(this.mockServer)
                    .then(function() {
                        view.$extraVideosBar.removeClass('is-visible');
                        view.openExtraVideosBar();
                        expect(view.$extraVideosBar).toHaveClass('is-visible');
                    })
                    .always(done);
            });

            it('closeExtraVideosBar', function(done) {
                var view = createVideoListView(this.mockServer);
                waitsForResponse(this.mockServer)
                    .then(function() {
                        view.$extraVideosBar.addClass('is-visible');
                        view.closeExtraVideosBar();

                        expect(view.$extraVideosBar).not.toHaveClass('is-visible');
                    })
                    .always(done);
            });

            it('toggleExtraVideosBar', function(done) {
                var view = createVideoListView(this.mockServer);
                waitsForResponse(this.mockServer)
                    .then(function() {
                        view.$extraVideosBar.addClass('is-visible');
                        view.toggleExtraVideosBar();
                        expect(view.$extraVideosBar).not.toHaveClass('is-visible');
                        view.toggleExtraVideosBar();
                        expect(view.$extraVideosBar).toHaveClass('is-visible');
                    })
                    .always(done);
            });

            it('getValueFromEditor', function(done) {
                var view = createVideoListView(this.mockServer);
                waitsForResponse(this.mockServer)
                    .then(function() {
                        expect(view).assertValueInView(modelStub.value);
                    })
                    .always(done);
            });

            it('setValueInEditor', function(done) {
                var view = createVideoListView(this.mockServer);
                waitsForResponse(this.mockServer)
                    .then(function() {
                        expect(view).assertCanUpdateView(['abc.mp4']);
                    })
                    .always(done);
            });

            it('getVideoObjectsList', function(done) {
                var view = createVideoListView(this.mockServer);
                var value = [
                    {
                        mode: 'youtube',
                        type: 'youtube',
                        video: '12345678901'
                    },
                    {
                        mode: 'html5',
                        type: 'mp4',
                        video: 'video'
                    },
                    {
                        mode: 'html5',
                        type: 'other',
                        video: 'pxxZrg'
                    }
                ];

                waitsForResponse(this.mockServer)
                    .then(function() {
                        view.setValueInEditor([
                            'http://youtu.be/12345678901',
                            'video.mp4',
                            'http://goo.gl/pxxZrg',
                            'video'
                        ]);
                        expect(view).assertIsCorrectVideoList(value);
                    })
                    .always(done);
            });

            describe('getPlaceholders', function() {
                it('All works okay if empty values are passed', function(done) {
                    var view = createVideoListView(this.mockServer),
                        defaultPlaceholders = view.placeholders;

                    waitsForResponse(this.mockServer)
                        .then(function() {
                            var result = view.getPlaceholders([]),
                                expectedResult = _.values(defaultPlaceholders).reverse();

                            expect(result).toEqual(expectedResult);
                        })
                        .always(done);
                });

                it('On filling less than 3 fields, remaining fields should have ' +
'placeholders for video types that were not filled yet',
                function(done) {
                    var view = createVideoListView(this.mockServer),
                        defaultPlaceholders = view.placeholders;
                    var dataDict = {
                        youtube: {
                            value: [modelStub.value[0]],
                            expectedResult: [
                                defaultPlaceholders.youtube,
                                defaultPlaceholders.mp4,
                                defaultPlaceholders.webm
                            ]
                        },
                        mp4: {
                            value: [modelStub.value[1]],
                            expectedResult: [
                                defaultPlaceholders.mp4,
                                defaultPlaceholders.youtube,
                                defaultPlaceholders.webm
                            ]
                        },
                        webm: {
                            value: [modelStub.value[2]],
                            expectedResult: [
                                defaultPlaceholders.webm,
                                defaultPlaceholders.youtube,
                                defaultPlaceholders.mp4
                            ]
                        }
                    };

                    defaultPlaceholders = view.placeholders;
                    waitsForResponse(this.mockServer)
                        .then(function() {
                            $.each(dataDict, function(index, val) {
                                var result = view.getPlaceholders(val.value);

                                expect(result).toEqual(val.expectedResult);
                            });
                        })
                        .always(done);
                }
                );
            });

            describe('inputHandler', function() {
                var eventObject;

                var resetSpies = function(view) {
                    MessageManager.prototype.hideError.calls.reset();
                    view.updateModel.calls.reset();
                    view.closeExtraVideosBar.calls.reset();
                };

                var setUp = function(view) {
                    eventObject = jQuery.Event('input');

                    spyOn(view, 'updateModel');
                    spyOn(view, 'closeExtraVideosBar');
                    spyOn(view, 'checkValidity');
                    spyOn($.fn, 'hasClass');
                    spyOn($.fn, 'addClass');
                    spyOn($.fn, 'removeClass');
                    spyOn($.fn, 'prop').and.callThrough();
                    spyOn(_, 'isEqual');

                    resetSpies(view);
                };

                var videoListView = function() {
                    return new VideoList({
                        el: $('.component'),
                        model: new MetadataModel(modelStub),
                        MessageManager: MessageManager
                    });
                };

                beforeEach(function() {
                    MessageManager.prototype.render.and.callFake(function() { return true; });
                });

                afterEach(function() {
                    MessageManager.prototype.render.and.callThrough();
                });

                it('Field has invalid value - nothing should happen', function() {
                    var view = videoListView();
                    setUp(view);
                    $.fn.hasClass.and.returnValue(false);
                    view.checkValidity.and.returnValue(false);

                    view.inputHandler(eventObject);
                    expect(MessageManager.prototype.hideError).not.toHaveBeenCalled();
                    expect(view.updateModel).not.toHaveBeenCalled();
                    expect(view.closeExtraVideosBar).not.toHaveBeenCalled();
                    expect($.fn.prop).toHaveBeenCalledWith('disabled', true);
                    expect($.fn.addClass).toHaveBeenCalledWith('is-disabled');
                });

                it('Main field has invalid value - extra Videos Bar is closed', function() {
                    var view = videoListView();
                    setUp(view);
                    $.fn.hasClass.and.returnValue(true);
                    view.checkValidity.and.returnValue(false);

                    view.inputHandler(eventObject);
                    expect(MessageManager.prototype.hideError).not.toHaveBeenCalled();
                    expect(view.updateModel).not.toHaveBeenCalled();
                    expect(view.closeExtraVideosBar).toHaveBeenCalled();
                    expect($.fn.prop).toHaveBeenCalledWith('disabled', true);
                    expect($.fn.addClass).toHaveBeenCalledWith('is-disabled');
                });

                it('Model is updated if value is valid', function() {
                    var view = videoListView();
                    setUp(view);
                    view.checkValidity.and.returnValue(true);
                    _.isEqual.and.returnValue(false);

                    view.inputHandler(eventObject);
                    expect(MessageManager.prototype.hideError).not.toHaveBeenCalled();
                    expect(view.updateModel).toHaveBeenCalled();
                    expect(view.closeExtraVideosBar).not.toHaveBeenCalled();
                    expect($.fn.prop).toHaveBeenCalledWith('disabled', false);
                    expect($.fn.removeClass).toHaveBeenCalledWith('is-disabled');
                });

                it('Corner case: Error is hided', function() {
                    var view = videoListView();
                    setUp(view);
                    view.checkValidity.and.returnValue(true);
                    _.isEqual.and.returnValue(true);

                    view.inputHandler(eventObject);
                    expect(MessageManager.prototype.hideError).toHaveBeenCalled();
                    expect(view.updateModel).not.toHaveBeenCalled();
                    expect(view.closeExtraVideosBar).not.toHaveBeenCalled();
                    expect($.fn.prop).toHaveBeenCalledWith('disabled', false);
                    expect($.fn.removeClass).toHaveBeenCalledWith('is-disabled');
                });
            });
        });
    });
