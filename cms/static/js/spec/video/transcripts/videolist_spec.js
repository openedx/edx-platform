define(
    [
        'jquery', 'underscore',
        'edx-ui-toolkit/js/utils/spec-helpers/ajax-helpers',
        'js/views/video/transcripts/utils',
        'js/views/video/transcripts/metadata_videolist', 'js/models/metadata',
        'js/views/abstract_editor',
        'xmodule'
    ],
function ($, _, AjaxHelpers, Utils, VideoList, MetadataModel, AbstractEditor) {
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


        var createMockAjaxServer = function () {
            var mockServer = AjaxHelpers.server(
                [
                    200,
                    { 'Content-Type': 'application/json'},
                    response
                ]
            );
            mockServer.autoRespond = true;
            return mockServer;
        };

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

            // create mock server
            this.mockServer = createMockAjaxServer();

            spyOn(Utils, 'command').and.callThrough();
            spyOn(abstractEditor, 'initialize').and.callThrough();
            spyOn(abstractEditor, 'render').and.callThrough();
            spyOn(console, 'error');

            messenger = jasmine.createSpyObj('MessageManager',[
                'initialize', 'render', 'showError', 'hideError'
            ]);

            $.each(messenger, function(index, method) {
                 method.and.returnValue(messenger);
            });

            MessageManager = function () {
                messenger.initialize();

                return messenger;
            };

            jasmine.addMatchers({
                assertValueInView: function() {
                    return {
                        compare: function (actual, expected) {
                            var actualValue = actual.getValueFromEditor(),
                            passed = _.isEqual(actualValue, expected);

                            return {
                                pass: passed
                            };
                        }
                    };
                },
                assertCanUpdateView: function () {
                    return {
                        compare: function (actual, expected) {
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
                assertIsCorrectVideoList: function () {
                    return {
                        compare: function (actual, expected) {
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

        afterEach(function () {
            // restore mock server
            this.mockServer.restore();
        });

        var createVideoListView = function () {
            var model = new MetadataModel(modelStub);
            return new VideoList({
                el: $('.component'),
                model: model,
                MessageManager: MessageManager
            });
        };

        var waitsForResponse = function (mockServer) {
            return jasmine.waitUntil(function () {
                var requests = mockServer.requests,
                    len = requests.length;

                return len && requests[0].readyState === 4;
            });
        };


        it('Initialize', function (done) {
            var view = createVideoListView();
            waitsForResponse(this.mockServer)
              .then(function () {
                  expect(abstractEditor.initialize).toHaveBeenCalled();
                  expect(messenger.initialize).toHaveBeenCalled();
                  expect(view.component_locator).toBe(component_locator);
                  expect(view.$el).toHandle('input');
              }).always(done);
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
                    abstractEditor.render.calls.reset();
                    Utils.command.calls.reset();
                    messenger.render.calls.reset();
                    mockServer.requests.length = 0;
                };

            it('is rendered in correct way', function (done) {
                createVideoListView();
                waitsForResponse(this.mockServer)
                  .then(function () {
                      assertToHaveBeenRendered(videoList);
                  })
                  .always(done);
            });

            it('is rendered with opened extra videos bar', function (done) {
                var view = createVideoListView();
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

                spyOn(view, 'getVideoObjectsList').and.returnValue(videoListLength);
                spyOn(view, 'openExtraVideosBar');

                resetSpies(this.mockServer);
                view.render();

                waitsForResponse(this.mockServer)
                    .then(function () {
                        assertToHaveBeenRendered(videoListLength);
                        view.getVideoObjectsList.and.returnValue(videoListLength);
                        expect(view.openExtraVideosBar).toHaveBeenCalled();
                    })
                    .then(_.bind(function () {
                        resetSpies(this.mockServer);
                        view.openExtraVideosBar.calls.reset();
                        view.getVideoObjectsList.and.returnValue(videoListHtml5mode);
                        view.render();

                        return waitsForResponse(this.mockServer)
                            .then(function () {
                                assertToHaveBeenRendered(videoListHtml5mode);
                                expect(view.openExtraVideosBar).toHaveBeenCalled();
                            }).then(done);
                    }, this));

            });

            it('is rendered without opened extra videos bar', function (done) {
                var view = createVideoListView(),
                    videoList = [
                        {
                            mode: 'youtube',
                            type: 'youtube',
                            video: '12345678901'
                        }
                    ];

                spyOn(view, 'getVideoObjectsList').and.returnValue(videoList);
                spyOn(view, 'closeExtraVideosBar');

                resetSpies(this.mockServer);
                view.render();

                waitsForResponse(this.mockServer)
                  .then(function () {
                      assertToHaveBeenRendered(videoList);
                      expect(view.closeExtraVideosBar).toHaveBeenCalled();
                  })
                  .always(done);
            });
        });

        describe('isUniqOtherVideos', function () {
            it('Unique data - return true', function (done) {
                var view = createVideoListView(),
                    data = videoList.concat([{
                        mode: 'html5',
                        type: 'other',
                        video: 'pxxZrg'
                    }]);

                waitsForResponse(this.mockServer)
                  .then(function () {
                      var result = view.isUniqOtherVideos(data);
                      expect(result).toBe(true);
                  })
                  .always(done);
            });

            it('Not Unique data - return false', function (done) {
                var view = createVideoListView(),
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
                  .then(function () {
                      var result = view.isUniqOtherVideos(data);
                      expect(result).toBe(false);
                  })
                  .always(done);
            });
        });

        describe('isUniqVideoTypes', function () {
            it('Unique data - return true', function (done) {
                var view = createVideoListView(),
                    data = videoList;

                waitsForResponse(this.mockServer)
                  .then(function () {
                      var result = view.isUniqVideoTypes(data);
                      expect(result).toBe(true);
                  })
                  .always(done);
            });

            it('Not Unique data - return false', function (done) {
                var view = createVideoListView(),
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
                  .then(function () {
                      var result = view.isUniqVideoTypes(data);
                      expect(result).toBe(false);
                  })
                  .always(done);
            });
        });

        describe('checkIsUniqVideoTypes', function () {
            it('Error is shown', function (done) {
                var view = createVideoListView(),
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
                  .then(function () {
                      var result = view.checkIsUniqVideoTypes(data);

                      expect(messenger.showError).toHaveBeenCalled();
                      expect(result).toBe(false);
                  })
                  .always(done);
            });

            it('All works okay if arguments are not passed', function (done) {
                var view = createVideoListView();
                spyOn(view, 'getVideoObjectsList').and.returnValue(videoList);

                waitsForResponse(this.mockServer)
                  .then(function () {
                      var result = view.checkIsUniqVideoTypes();

                      expect(view.getVideoObjectsList).toHaveBeenCalled();
                      expect(messenger.showError).not.toHaveBeenCalled();
                      expect(result).toBe(true);
                  })
                  .always(done);
            });
        });

        describe('checkValidity', function () {
            it('Error message is shown', function (done) {
                var view = createVideoListView();
                spyOn(view, 'checkIsUniqVideoTypes').and.returnValue(true);

                waitsForResponse(this.mockServer)
                  .then(function () {
                      var data = {mode: 'incorrect'},
                        result = view.checkValidity(data, true);

                      expect(messenger.showError).toHaveBeenCalled();
                      expect(view.checkIsUniqVideoTypes).toHaveBeenCalled();
                      expect(result).toBe(false);
                  })
                  .always(done);
            });

            it('Error message is shown when flag is not passed', function (done) {
                var view = createVideoListView();
                spyOn(view, 'checkIsUniqVideoTypes').and.returnValue(true);

                waitsForResponse(this.mockServer)
                  .then(function () {
                      var data = {mode: 'incorrect'},
                        result = view.checkValidity(data);

                      expect(messenger.showError).not.toHaveBeenCalled();
                      expect(view.checkIsUniqVideoTypes).toHaveBeenCalled();
                      expect(result).toBe(true);
                  }).always(done);
            });

            it('All works okay if correct data is passed', function (done) {
                var view = createVideoListView();
                spyOn(view, 'checkIsUniqVideoTypes').and.returnValue(true);

                waitsForResponse(this.mockServer)
                  .then(function () {
                      var data = videoList,
                        result = view.checkValidity(data);

                      expect(messenger.showError).not.toHaveBeenCalled();
                      expect(view.checkIsUniqVideoTypes).toHaveBeenCalled();
                      expect(result).toBe(true);
                  })
                  .always(done);
            });
        });

        it('openExtraVideosBar', function (done) {
            var view = createVideoListView();
            waitsForResponse(this.mockServer)
              .then(function () {
                  view.$extraVideosBar.removeClass('is-visible');
                  view.openExtraVideosBar();
                  expect(view.$extraVideosBar).toHaveClass('is-visible');
              })
              .always(done);
        });

        it('closeExtraVideosBar', function (done) {
            var view = createVideoListView();
            waitsForResponse(this.mockServer)
              .then(function () {
                  view.$extraVideosBar.addClass('is-visible');
                  view.closeExtraVideosBar();

                  expect(view.$extraVideosBar).not.toHaveClass('is-visible');
              })
              .always(done);
        });

        it('toggleExtraVideosBar', function (done) {
            var view = createVideoListView();
            waitsForResponse(this.mockServer)
              .then(function () {
                  view.$extraVideosBar.addClass('is-visible');
                  view.toggleExtraVideosBar();
                  expect(view.$extraVideosBar).not.toHaveClass('is-visible');
                  view.toggleExtraVideosBar();
                  expect(view.$extraVideosBar).toHaveClass('is-visible');
              })
              .always(done);
        });

        it('getValueFromEditor', function (done) {
            var view = createVideoListView();
            waitsForResponse(this.mockServer)
              .then(function () {
                  expect(view).assertValueInView(modelStub.value);
              })
              .always(done);
        });

        it('setValueInEditor', function (done) {
            var view = createVideoListView();
            waitsForResponse(this.mockServer)
              .then(function () {
                  expect(view).assertCanUpdateView(['abc.mp4']);
              })
              .always(done);
        });

        it('getVideoObjectsList', function (done) {
            var view = createVideoListView();
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
              .then(function () {
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

        describe('getPlaceholders', function () {

            it('All works okay if empty values are passed', function (done) {
                var view = createVideoListView(),
                    defaultPlaceholders = view.placeholders;

                waitsForResponse(this.mockServer)
                  .then(function () {
                      var result = view.getPlaceholders([]),
                        expectedResult = _.values(defaultPlaceholders).reverse();

                      expect(result).toEqual(expectedResult);
                  })
                  .always(done);
            });

            it('On filling less than 3 fields, remaining fields should have ' +
'placeholders for video types that were not filled yet',
                function (done) {
                    var view = createVideoListView(),
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
                      .then(function () {
                          $.each(dataDict, function (index, val) {
                              var result = view.getPlaceholders(val.value);

                              expect(result).toEqual(val.expectedResult);
                          });
                      })
                      .always(done);
                }
            );
        });

        describe('inputHandler', function () {
            var eventObject;

            var resetSpies = function (view) {
                messenger.hideError.calls.reset();
                view.updateModel.calls.reset();
                view.closeExtraVideosBar.calls.reset();
            };

            var setUp = function (view) {
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

            it('Field has invalid value - nothing should happen',
                function (done) {
                    var view = createVideoListView();
                    setUp(view);
                    $.fn.hasClass.and.returnValue(false);
                    view.checkValidity.and.returnValue(false);

                    waitsForResponse(this.mockServer)
                        .then(function () {
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
                        })
                        .always(done);
                }
            );

            it('Main field has invalid value - extra Videos Bar is closed',
                function (done) {
                    var view = createVideoListView();
                    setUp(view);
                    $.fn.hasClass.and.returnValue(true);
                    view.checkValidity.and.returnValue(false);

                    waitsForResponse(this.mockServer)
                        .then(function () {
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
                        })
                        .always(done);
                }
            );

            it('Model is updated if value is valid',
                function (done) {
                    var view = createVideoListView();
                    setUp(view);
                    view.checkValidity.and.returnValue(true);
                    _.isEqual.and.returnValue(false);

                    waitsForResponse(this.mockServer)
                        .then(function () {
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
                        })
                        .always(done);
                }
            );

            it('Corner case: Error is hided',
                function (done) {
                    var view = createVideoListView();
                    setUp(view);
                    view.checkValidity.and.returnValue(true);
                    _.isEqual.and.returnValue(true);
                    waitsForResponse(this.mockServer)
                        .then(function () {
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
                        })
                        .always(done);
                }
            );

        });

    });
});
