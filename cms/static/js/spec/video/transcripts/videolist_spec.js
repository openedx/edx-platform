define(
    [
        'jquery', 'underscore',
        'js/views/video/transcripts/utils',
        'js/views/video/transcripts/metadata_videolist', 'js/models/metadata',
        'js/views/abstract_editor',
        'common/js/spec_helpers/ajax_helpers',
        'xmodule', 'jasmine-jquery'
    ],
function ($, _, Utils, VideoList, MetadataModel, AbstractEditor, AjaxHelpers) {
    'use strict';
    describe('CMS.Views.Metadata.VideoList', function () {
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
            response = JSON.stringify({
                command: 'found',
                status: 'Success',
                subs: 'video_id'
            }),
            MessageManager, messenger;

        beforeEach(function () {
            var tpl = sandbox({
                    'class': 'component',
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

            spyOn(Utils, 'command').andCallThrough();
            spyOn(abstractEditor, 'initialize').andCallThrough();
            spyOn(abstractEditor, 'render').andCallThrough();
            spyOn(console, 'error');

            messenger = jasmine.createSpyObj('MessageManager',[
                'initialize', 'render', 'showError', 'hideError'
            ]);

            $.each(messenger, function(index, method) {
                 method.andReturn(messenger);
            });

            MessageManager = function () {
                messenger.initialize();

                return messenger;
            };

            this.addMatchers({
                assertValueInView: function(expected) {
                    var actualValue = this.actual.getValueFromEditor();
                    return this.env.equals_(actualValue, expected);
                },
                assertCanUpdateView: function (expected) {
                    var actual = this.actual,
                        actualValue;

                    actual.setValueInEditor(expected);
                    actualValue = actual.getValueFromEditor();

                    return this.env.equals_(actualValue, expected);
                },
                assertIsCorrectVideoList: function (expected) {
                    var actualValue = this.actual.getVideoObjectsList();

                    return this.env.equals_(actualValue, expected);
                }
            });
        });

        var createMockAjaxServer = function (test) {
            var mockServer = AjaxHelpers.server(
                test,
                [
                    200,
                    { 'Content-Type': 'application/json'},
                    response
                ]
            );
            mockServer.autoRespond = true;
            return mockServer;
        };

        var createVideoListView = function () {
            var model = new MetadataModel(modelStub);
            return new VideoList({
                el: $('.component'),
                model: model,
                MessageManager: MessageManager
            });
        };

        var waitsForResponse = function (mockServer, expectFunc, prep) {
            var flag = false;

            if (prep) {
                runs(prep);
            }

            waitsFor(function() {
                var requests = mockServer.requests,
                    len = requests.length;

                if (len && requests[0].readyState === 4) {
                    flag = true;
                }

                return flag;
            }, 'Ajax Timeout', 750);

            runs(expectFunc);
        };


        it('Initialize', function () {
            var mockServer = createMockAjaxServer(this),
                view = createVideoListView();
            waitsForResponse(mockServer, function () {
                expect(abstractEditor.initialize).toHaveBeenCalled();
                expect(messenger.initialize).toHaveBeenCalled();
                expect(view.component_locator).toBe(component_locator);
                expect(view.$el).toHandle('input');
            });
        });

        describe('Render', function () {
            var assertToHaveBeenRendered = function (videoList) {
                    expect(abstractEditor.render).toHaveBeenCalled();
                    expect(Utils.command).toHaveBeenCalledWith(
                        'check',
                        component_locator,
                        videoList
                    );

                    expect(messenger.render).toHaveBeenCalled();
                },
                resetSpies = function(mockServer) {
                    abstractEditor.render.reset();
                    Utils.command.reset();
                    messenger.render.reset();
                    mockServer.requests.length = 0;
                };

            it('is rendered in correct way', function () {
                var mockServer = createMockAjaxServer(this);
                createVideoListView();
                waitsForResponse(mockServer, function () {
                    assertToHaveBeenRendered(videoList);
                });
            });

            it('is rendered with opened extra videos bar', function () {
                var mockServer = createMockAjaxServer(this),
                    view = createVideoListView();
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

                spyOn(view, 'getVideoObjectsList').andReturn(videoListLength);
                spyOn(view, 'openExtraVideosBar');

                waitsForResponse(
                    mockServer,
                    function () {
                        assertToHaveBeenRendered(videoListLength);
                        view.getVideoObjectsList.andReturn(videoListLength);
                        expect(view.openExtraVideosBar).toHaveBeenCalled();
                    },
                    function () {
                        resetSpies(mockServer);
                        view.render();
                    }
                );

                waitsForResponse(
                    mockServer,
                    function () {
                        assertToHaveBeenRendered(videoListHtml5mode);
                        expect(view.openExtraVideosBar).toHaveBeenCalled();
                    },
                    function () {
                        resetSpies(mockServer);
                        view.openExtraVideosBar.reset();
                        view.getVideoObjectsList.andReturn(videoListHtml5mode);
                        view.render();
                    }
                );

            });

            it('is rendered without opened extra videos bar', function () {
                var mockServer = createMockAjaxServer(this),
                    view = createVideoListView(),
                    videoList = [
                        {
                            mode: 'youtube',
                            type: 'youtube',
                            video: '12345678901'
                        }
                    ];

                spyOn(view, 'getVideoObjectsList').andReturn(videoList);
                spyOn(view, 'closeExtraVideosBar');

                waitsForResponse(
                    mockServer,
                    function () {
                        assertToHaveBeenRendered(videoList);
                        expect(view.closeExtraVideosBar).toHaveBeenCalled();
                    },
                    function () {
                        resetSpies(mockServer);
                        view.render();
                    }
                );
            });

        });

        describe('isUniqOtherVideos', function () {
            it('Unique data - return true', function () {
                var mockServer = createMockAjaxServer(this),
                    view = createVideoListView(),
                    data = videoList.concat([{
                        mode: 'html5',
                        type: 'other',
                        video: 'pxxZrg'
                    }]);
                waitsForResponse(mockServer, function () {
                    var result = view.isUniqOtherVideos(data);

                    expect(result).toBe(true);
                });

            });

            it('Not Unique data - return false', function () {
                var mockServer = createMockAjaxServer(this),
                    view = createVideoListView(),
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
                waitsForResponse(mockServer, function () {
                    var result = view.isUniqOtherVideos(data);

                    expect(result).toBe(false);
                });
            });
        });

        describe('isUniqVideoTypes', function () {

            it('Unique data - return true', function () {
                var mockServer = createMockAjaxServer(this),
                    view = createVideoListView(),
                    data = videoList;
                waitsForResponse(mockServer, function () {
                    var result = view.isUniqVideoTypes(data);
                    expect(result).toBe(true);
                });

            });

            it('Not Unique data - return false', function () {
                var mockServer = createMockAjaxServer(this),
                    view = createVideoListView(),
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
                waitsForResponse(mockServer, function () {
                    var result = view.isUniqVideoTypes(data);

                    expect(result).toBe(false);
                });
            });
        });

        describe('checkIsUniqVideoTypes', function () {
            it('Error is shown', function () {
                var mockServer = createMockAjaxServer(this),
                    view = createVideoListView(),
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

                waitsForResponse(mockServer, function () {
                    var result = view.checkIsUniqVideoTypes(data);

                    expect(messenger.showError).toHaveBeenCalled();
                    expect(result).toBe(false);
                });
            });

            it('All works okay if arguments are not passed', function () {
                var mockServer = createMockAjaxServer(this),
                    view = createVideoListView();
                spyOn(view, 'getVideoObjectsList').andReturn(videoList);
                waitsForResponse(mockServer, function () {
                    var result = view.checkIsUniqVideoTypes();

                    expect(view.getVideoObjectsList).toHaveBeenCalled();
                    expect(messenger.showError).not.toHaveBeenCalled();
                    expect(result).toBe(true);
                });
            });
        });

        describe('checkValidity', function () {
            it('Error message is shown', function () {
                var mockServer = createMockAjaxServer(this),
                    view = createVideoListView();
                spyOn(view, 'checkIsUniqVideoTypes').andReturn(true);
                waitsForResponse(mockServer, function () {
                    var data = { mode: 'incorrect' },
                        result = view.checkValidity(data, true);

                    expect(messenger.showError).toHaveBeenCalled();
                    expect(view.checkIsUniqVideoTypes).toHaveBeenCalled();
                    expect(result).toBe(false);
                });
            });

            it('Error message is shown when flag is not passed', function () {
                var mockServer = createMockAjaxServer(this),
                    view = createVideoListView();
                spyOn(view, 'checkIsUniqVideoTypes').andReturn(true);
                waitsForResponse(mockServer, function () {
                    var data = { mode: 'incorrect' },
                        result = view.checkValidity(data);

                    expect(messenger.showError).not.toHaveBeenCalled();
                    expect(view.checkIsUniqVideoTypes).toHaveBeenCalled();
                    expect(result).toBe(true);
                });
            });

            it('All works okay if correct data is passed', function () {
                var mockServer = createMockAjaxServer(this),
                    view = createVideoListView();
                spyOn(view, 'checkIsUniqVideoTypes').andReturn(true);
                waitsForResponse(mockServer, function () {
                    var data = videoList,
                        result = view.checkValidity(data);

                    expect(messenger.showError).not.toHaveBeenCalled();
                    expect(view.checkIsUniqVideoTypes).toHaveBeenCalled();
                    expect(result).toBe(true);
                });
            });
        });

        it('openExtraVideosBar', function () {
            var mockServer = createMockAjaxServer(this),
                view = createVideoListView();
            waitsForResponse(mockServer, function () {
                view.$extraVideosBar.removeClass('is-visible');

                view.openExtraVideosBar();
                expect(view.$extraVideosBar).toHaveClass('is-visible');
            });
        });

        it('closeExtraVideosBar', function () {
            var mockServer = createMockAjaxServer(this),
                view = createVideoListView();
            waitsForResponse(mockServer, function () {
                view.$extraVideosBar.addClass('is-visible');
                view.closeExtraVideosBar();

                expect(view.$extraVideosBar).not.toHaveClass('is-visible');
            });
        });

        it('toggleExtraVideosBar', function () {
            var mockServer = createMockAjaxServer(this),
                view = createVideoListView();
            waitsForResponse(mockServer, function () {
                view.$extraVideosBar.addClass('is-visible');
                view.toggleExtraVideosBar();
                expect(view.$extraVideosBar).not.toHaveClass('is-visible');
                view.toggleExtraVideosBar();
                expect(view.$extraVideosBar).toHaveClass('is-visible');
            });
        });

        it('getValueFromEditor', function () {
            var mockServer = createMockAjaxServer(this),
                view = createVideoListView();
            waitsForResponse(mockServer, function () {
                expect(view).assertValueInView(modelStub.value);
            });
        });

        it('setValueInEditor', function () {
            var mockServer = createMockAjaxServer(this),
                view = createVideoListView();
            waitsForResponse(mockServer, function () {
                expect(view).assertCanUpdateView(['abc.mp4']);
            });
        });

        it('getVideoObjectsList', function () {
            var mockServer = createMockAjaxServer(this),
                view = createVideoListView();
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

            waitsForResponse(mockServer, function () {
                view.setValueInEditor([
                    'http://youtu.be/12345678901',
                    'video.mp4',
                    'http://goo.gl/pxxZrg',
                    'video'
                ]);
                expect(view).assertIsCorrectVideoList(value);
            });
        });

        describe('getPlaceholders', function () {

            it('All works okay if empty values are passed', function () {
                var mockServer = createMockAjaxServer(this),
                    view = createVideoListView(),
                    defaultPlaceholders = view.placeholders;
                waitsForResponse(mockServer, function () {
                    var result = view.getPlaceholders([]),
                    expectedResult = _.values(defaultPlaceholders).reverse();

                    expect(result).toEqual(expectedResult);
                });
            });

            it('On filling less than 3 fields, remaining fields should have ' +
'placeholders for video types that were not filled yet',
                function () {
                    var mockServer = createMockAjaxServer(this),
                        view = createVideoListView(),
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
                    waitsForResponse(mockServer, function () {
                        $.each(dataDict, function(index, val) {
                            var result = view.getPlaceholders(val.value);

                            expect(result).toEqual(val.expectedResult);
                        });
                    });
                }
            );
        });

        describe('inputHandler', function () {
            var eventObject;

            var resetSpies = function (view) {
                messenger.hideError.reset();
                view.updateModel.reset();
                view.closeExtraVideosBar.reset();
            };

            var setUp = function (view) {
                eventObject = jQuery.Event('input');

                spyOn(view, 'updateModel');
                spyOn(view, 'closeExtraVideosBar');
                spyOn(view, 'checkValidity');
                spyOn($.fn, 'hasClass');
                spyOn($.fn, 'addClass');
                spyOn($.fn, 'removeClass');
                spyOn($.fn, 'prop').andCallThrough();
                spyOn(_, 'isEqual');

                resetSpies(view);
            };

            it('Field has invalid value - nothing should happen',
                function () {
                    var mockServer = createMockAjaxServer(this),
                        view = createVideoListView();
                    setUp(view);
                    $.fn.hasClass.andReturn(false);
                    view.checkValidity.andReturn(false);

                    waitsForResponse(mockServer, function () {
                        view.inputHandler(eventObject);
                        expect(messenger.hideError).not.toHaveBeenCalled();
                        expect(view.updateModel).not.toHaveBeenCalled();
                        expect(view.closeExtraVideosBar).not.toHaveBeenCalled();
                        expect($.fn.prop).toHaveBeenCalledWith(
                            'disabled', true
                        );
                        expect($.fn.addClass).toHaveBeenCalledWith(
                            'is-disabled'
                        );
                    });
                }
            );

            it('Main field has invalid value - extra Videos Bar is closed',
                function () {
                    var mockServer = createMockAjaxServer(this),
                        view = createVideoListView();
                    setUp(view);
                    $.fn.hasClass.andReturn(true);
                    view.checkValidity.andReturn(false);

                    waitsForResponse(mockServer, function () {
                        view.inputHandler(eventObject);
                        expect(messenger.hideError).not.toHaveBeenCalled();
                        expect(view.updateModel).not.toHaveBeenCalled();
                        expect(view.closeExtraVideosBar).toHaveBeenCalled();
                        expect($.fn.prop).toHaveBeenCalledWith(
                            'disabled', true
                        );
                        expect($.fn.addClass).toHaveBeenCalledWith(
                            'is-disabled'
                        );
                    });
                }
            );

            it('Model is updated if value is valid',
                function () {
                    var mockServer = createMockAjaxServer(this),
                        view = createVideoListView();
                    setUp(view);
                    view.checkValidity.andReturn(true);
                    _.isEqual.andReturn(false);

                    waitsForResponse(mockServer, function () {
                        view.inputHandler(eventObject);
                        expect(messenger.hideError).not.toHaveBeenCalled();
                        expect(view.updateModel).toHaveBeenCalled();
                        expect(view.closeExtraVideosBar).not.toHaveBeenCalled();
                        expect($.fn.prop).toHaveBeenCalledWith(
                            'disabled', false
                        );
                        expect($.fn.removeClass).toHaveBeenCalledWith(
                            'is-disabled'
                        );
                    });
                }
            );

            it('Corner case: Error is hided',
                function () {
                    var mockServer = createMockAjaxServer(this),
                        view = createVideoListView();
                    setUp(view);
                    view.checkValidity.andReturn(true);
                    _.isEqual.andReturn(true);
                    waitsForResponse(mockServer, function () {
                        view.inputHandler(eventObject);
                        expect(messenger.hideError).toHaveBeenCalled();
                        expect(view.updateModel).not.toHaveBeenCalled();
                        expect(view.closeExtraVideosBar).not.toHaveBeenCalled();
                        expect($.fn.prop).toHaveBeenCalledWith(
                            'disabled', false
                        );
                        expect($.fn.removeClass).toHaveBeenCalledWith(
                            'is-disabled'
                        );
                    });
                }
            );

        });

    });
});
