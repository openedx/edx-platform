(function(undefined) {
    describe('Video', function() {
        afterEach(function() {
            $('source').remove();
            window.VideoState = {};
            window.VideoState.id = {};
            window.YT = jasmine.YT;
        });

        describe('constructor', function() {
            describe('YT', function() {
                var state;

                beforeEach(function() {
                    loadFixtures('video.html');
                    $.cookie.and.returnValue('0.50');
                });

                describe('by default', function() {
                    beforeEach(function() {
                        state = jasmine.initializePlayerYouTube('video_html5.html');
                    });

                    afterEach(function() {
                        state.storage.clear();
                        state.videoPlayer.destroy();
                    });

                    it('check videoType', function() {
                        expect(state.videoType).toEqual('youtube');
                    });

                    it('set the elements', function() {
                        expect(state.el).toEqual($('#video_id'));
                    });

                    it('parse the videos', function() {
                        expect(state.videos).toEqual({
                            '0.50': '7tqY6eQzVhE',
                            '1.0': 'cogebirgzzM',
                            '1.50': 'abcdefghijkl'
                        });
                    });

                    it('parse available video speeds', function() {
                        expect(state.speeds).toEqual(['0.50', '1.0', '1.50']);
                    });

                    it('set current video speed via cookie', function() {
                        expect(state.speed).toEqual('1.50');
                    });
                });
            });

            describe('HTML5', function() {
                var state;

                beforeEach(function() {
                    $.cookie.and.returnValue('0.75');
                    state = jasmine.initializePlayer('video_html5.html');
                });

                afterEach(function() {
                    state.storage.clear();
                    state.videoPlayer.destroy();
                });

                describe('by default', function() {
                    it('check videoType', function() {
                        expect(state.videoType).toEqual('html5');
                    });

                    it('set the elements', function() {
                        expect(state.el).toEqual($('#video_id'));
                    });

                    it('doesn\'t have `videos` dictionary', function() {
                        expect(state.videos).toBeUndefined();
                    });

                    it('parse available video speeds', function() {
                        var speeds = jasmine.stubbedHtml5Speeds;

                        expect(state.speeds).toEqual(speeds);
                    });

                    it('set current video speed via cookie', function() {
                        expect(state.speed).toEqual(1.5);
                    });
                });

                // Note that the loading of stand alone HTML5 player API is
                // handled by Require JS. When state.videoPlayer is created,
                // the stand alone HTML5 player object is already loaded, so no
                // further testing in that case is required.
                describe('HTML5 API is available', function() {
                    it('create the Video Player', function() {
                        expect(state.videoPlayer.player).not.toBeUndefined();
                    });
                });
            });
        });

        describe('YouTube API is not loaded', function() {
            var state;
            beforeEach(function() {
                window.YT = undefined;
                state = jasmine.initializePlayerYouTube();
            });

            afterEach(function() {
                state.storage.clear();
                state.videoPlayer.destroy();
            });

            it('callback, to be called after YouTube API loads, exists and is called', function(done) {
                window.YT = jasmine.YT;
                // Call the callback that must be called when YouTube API is
                // loaded. By specification.
                window.onYouTubeIframeAPIReady();
                jasmine.waitUntil(function() {
                    return state.youtubeApiAvailable === true;
                }).done(function() {
                    // If YouTube API is not loaded, then the code will should create
                    // a global callback that will be called by API once it is loaded.
                    expect(window.onYouTubeIframeAPIReady).not.toBeUndefined();
                }).always(done);
            });
        });

        describe('checking start and end times', function() {
            var state;
            var miniTestSuite = [
                {
                    itDescription: 'both times are proper',
                    data: {start: 12, end: 24},
                    expectData: {start: 12, end: 24}
                },
                {
                    itDescription: 'start time is invalid',
                    data: {start: '', end: 24},
                    expectData: {start: 0, end: 24}
                },
                {
                    itDescription: 'end time is invalid',
                    data: {start: 12, end: ''},
                    expectData: {start: 12, end: null}
                },
                {
                    itDescription: 'start time is less than 0',
                    data: {start: -12, end: 24},
                    expectData: {start: 0, end: 24}
                },
                {
                    itDescription: 'start time is greater than end time',
                    data: {start: 42, end: 24},
                    expectData: {start: 42, end: null}
                }
            ];

            afterEach(function() {
                state.storage.clear();
                state.videoPlayer.destroy();
            });

            $.each(miniTestSuite, function(index, test) {
                itFabrique(test.itDescription, test.data, test.expectData);
            });

            return;

            function itFabrique(itDescription, data, expectData) {
                it(itDescription, function() {
                    state = jasmine.initializePlayer('video.html', {
                        start: data.start,
                        end: data.end
                    });

                    expect(state.config.startTime).toBe(expectData.start);
                    expect(state.config.endTime).toBe(expectData.end);
                });
            }
        });

        // Disabled 11/25/13 due to flakiness in master
        xdescribe('multiple YT on page', function() {
            var state1, state2, state3;

            beforeEach(function() {
                loadFixtures('video_yt_multiple.html');

                spyOn($, 'ajaxWithPrefix');

                $.ajax.calls.length = 0;
                $.ajaxWithPrefix.calls.length = 0;

                // Because several other tests have run, the variable
                // that stores the value of the first ajax request must be
                // cleared so that we test a pristine state of the video
                // module.
                Video.clearYoutubeXhr();

                state1 = new Video('#example1');
                state2 = new Video('#example2');
                state3 = new Video('#example3');
            });

            it(
                'check for YT availability is performed only once',
                function() {
                    var numAjaxCalls = 0;

                // Total ajax calls made.
                    numAjaxCalls = $.ajax.calls.length;

                // Subtract ajax calls to get captions via
                // state.videoCaption.fetchCaption() function.
                    numAjaxCalls -= $.ajaxWithPrefix.calls.length;

                // Subtract ajax calls to get metadata for each video via
                // state.getVideoMetadata() function.
                    numAjaxCalls -= 3;

                // Subtract ajax calls to log event 'pause_video' via
                // state.videoPlayer.log() function.
                    numAjaxCalls -= 3;

                // This should leave just one call. It was made to check
                // for YT availability. This is done in state.initialize()
                // function. SPecifically, with the statement
                //
                //     this.youtubeXhr = this.getVideoMetadata();
                    expect(numAjaxCalls).toBe(1);
                });
        });
    });
}).call(this);
