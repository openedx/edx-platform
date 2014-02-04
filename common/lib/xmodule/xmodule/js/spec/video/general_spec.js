(function (undefined) {
    describe('Video', function () {
        var oldOTBD;

        beforeEach(function () {
            jasmine.stubRequests();
        });

        afterEach(function () {
            $('source').remove();
        });

        describe('constructor', function () {
            describe('YT', function () {
                beforeEach(function () {
                    loadFixtures('video.html');
                    $.cookie.andReturn('0.50');
                });

                describe('by default', function () {
                    beforeEach(function () {
                        this.state = new window.Video('#example');
                    });

                    it('check videoType', function () {
                        expect(this.state.videoType).toEqual('youtube');
                    });

                    it('set the elements', function () {
                        expect(this.state.el).toBe('#video_id');
                    });

                    it('parse the videos', function () {
                        expect(this.state.videos).toEqual({
                            '0.50': '7tqY6eQzVhE',
                            '1.0': 'cogebirgzzM',
                            '1.50': 'abcdefghijkl'
                        });
                    });

                    it('parse available video speeds', function () {
                        expect(this.state.speeds).toEqual(['0.50', '1.0', '1.50']);
                    });

                    it('set current video speed via cookie', function () {
                        expect(this.state.speed).toEqual('1.50');
                    });
                });
            });

            describe('HTML5', function () {
                var state;

                beforeEach(function () {
                    loadFixtures('video_html5.html');
                    $.cookie.andReturn('0.75');
                });

                describe('by default', function () {
                    beforeEach(function () {
                        state = new window.Video('#example');
                    });

                    afterEach(function () {
                        state = undefined;
                    });

                    it('check videoType', function () {
                        expect(state.videoType).toEqual('html5');
                    });

                    it('set the elements', function () {
                        expect(state.el).toBe('#video_id');
                    });

                    it('parse the videos if subtitles exist', function () {
                        var sub = 'Z5KLxerq05Y';

                        expect(state.videos).toEqual({
                            '0.75': sub,
                            '1.0': sub,
                            '1.25': sub,
                            '1.50': sub
                        });
                    });

                    it(
                        'parse the videos if subtitles do not exist',
                        function ()
                    {
                        var sub = '';

                        $('#example').find('.video').data('sub', '');
                        state = new window.Video('#example');

                        expect(state.videos).toEqual({
                            '0.75': sub,
                            '1.0': sub,
                            '1.25': sub,
                            '1.50': sub
                        });
                    });

                    it('parse Html5 sources', function () {
                        var html5Sources = {
                                mp4: null,
                                webm: null,
                                ogg: null
                            }, v = document.createElement('video');

                        if (
                            !!(
                                v.canPlayType &&
                                v.canPlayType(
                                    'video/webm; codecs="vp8, vorbis"'
                                ).replace(/no/, '')
                            )
                        ) {
                            html5Sources['webm'] =
                                'xmodule/include/fixtures/test.webm';
                        }

                        if (
                            !!(
                                v.canPlayType &&
                                v.canPlayType(
                                    'video/mp4; codecs="avc1.42E01E, ' +
                                    'mp4a.40.2"'
                                ).replace(/no/, '')
                            )
                        ) {
                            html5Sources['mp4'] =
                                'xmodule/include/fixtures/test.mp4';
                        }

                        if (
                            !!(
                                v.canPlayType &&
                                v.canPlayType(
                                    'video/ogg; codecs="theora"'
                                ).replace(/no/, '')
                            )
                        ) {
                            html5Sources['ogg'] =
                                'xmodule/include/fixtures/test.ogv';
                        }

                        expect(state.html5Sources).toEqual(html5Sources);
                    });

                    it('parse available video speeds', function () {
                        var speeds = jasmine.stubbedHtml5Speeds;

                        expect(state.speeds).toEqual(speeds);
                    });

                    it('set current video speed via cookie', function () {
                        expect(state.speed).toEqual('1.50');
                    });
                });

                // Note that the loading of stand alone HTML5 player API is
                // handled by Require JS. When state.videoPlayer is created,
                // the stand alone HTML5 player object is already loaded, so no
                // further testing in that case is required.
                describe('HTML5 API is available', function () {
                    beforeEach(function () {
                        state = new Video('#example');
                    });

                    afterEach(function () {
                        state = null;
                    });

                    it('create the Video Player', function () {
                        expect(state.videoPlayer.player).not.toBeUndefined();
                    });
                });
            });
        });

        describe('youtubeId', function () {
            beforeEach(function () {
                loadFixtures('video.html');
                $.cookie.andReturn('1.0');
                state = new Video('#example');
            });

            describe('with speed', function () {
                it('return the video id for given speed', function () {
                    expect(state.youtubeId('0.50'))
                        .toEqual('7tqY6eQzVhE');
                    expect(state.youtubeId('1.0'))
                        .toEqual('cogebirgzzM');
                    expect(state.youtubeId('1.50'))
                        .toEqual('abcdefghijkl');
                });
            });

            describe('without speed', function () {
                it('return the video id for current speed', function () {
                    expect(state.youtubeId()).toEqual('abcdefghijkl');
                });
            });

            describe('speed is absent in the list of video speeds', function () {
                it('return the video id for 1.0x speed', function () {
                    expect(state.youtubeId('0.0')).toEqual('cogebirgzzM');
                });
            });
        });

        describe('YouTube video in FireFox will cue first', function () {
            var oldUserAgent;

            beforeEach(function () {
                oldUserAgent = window.navigator.userAgent;
                window.navigator.userAgent = 'firefox';

                state = jasmine.initializePlayer('video.html', {
                  start: 10,
                  end: 30
                });
            });

            afterEach(function () {
                window.navigator.userAgent = oldUserAgent;
            });

            it('cue is called, skipOnEndedStartEndReset is set', function () {
                state.videoPlayer.updatePlayTime(10);
                expect(state.videoPlayer.player.cueVideoById).toHaveBeenCalledWith('cogebirgzzM', 10);
                expect(state.videoPlayer.skipOnEndedStartEndReset).toBe(true);
            });

            it('Handling cue state', function () {
                spyOn(state.videoPlayer, 'play');

                state.videoPlayer.startTime = 10;
                state.videoPlayer.onStateChange({data: 5});

                expect(state.videoPlayer.player.seekTo).toHaveBeenCalledWith(10, true);
                expect(state.videoPlayer.play).toHaveBeenCalled();
            });

            it('when cued, onEnded resets start and end time only the second time', function () {
                state.videoPlayer.skipOnEndedStartEndReset = true;
                state.videoPlayer.onEnded();
                expect(state.videoPlayer.startTime).toBe(10);
                expect(state.videoPlayer.endTime).toBe(30);

                state.videoPlayer.skipOnEndedStartEndReset = undefined;
                state.videoPlayer.onEnded();
                expect(state.videoPlayer.startTime).toBe(0);
                expect(state.videoPlayer.endTime).toBe(null);
            });
        });

        it('getCurrentLanguage', function () {
            loadFixtures('video.html');
            $('.video').data('transcript-language', 'de');
            state = new Video('#example');

            expect(state.getCurrentLanguage()).toBe('de');
            state.lang = null;
            expect(state.getCurrentLanguage()).toBe('en');
        });

        describe('checking start and end times', function () {
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

            beforeEach(function () {
                loadFixtures('video.html');

            });

            $.each(miniTestSuite, function (index, test) {
                itFabrique(test.itDescription, test.data, test.expectData);
            });

            return;

            function itFabrique(itDescription, data, expectData) {
                it(itDescription, function () {
                    $('#example').find('.video')
                        .data({
                            'start': data.start,
                            'end': data.end
                        });

                    state = new Video('#example');

                    expect(state.config.startTime).toBe(expectData.start);
                    expect(state.config.endTime).toBe(expectData.end);
                });
            }
        });

        // Disabled 11/25/13 due to flakiness in master
        xdescribe('multiple YT on page', function () {
            var state1, state2, state3;

            beforeEach(function () {
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
                function ()
            {
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

        describe('setSpeed', function () {

            describe('YT', function () {
                beforeEach(function () {
                    loadFixtures('video.html');
                    state = new Video('#example');
                });

                it('check mapping', function () {
                    var map = {
                        '0.75': '0.50',
                        '1.25': '1.50'
                    };

                    $.each(map, function(key, expected) {
                        state.setSpeed(key, true);
                        expect(state.speed).toBe(expected);
                    });
                });
            });
            describe('HTML5', function () {
                beforeEach(function () {
                    loadFixtures('video_html5.html');
                    state = new Video('#example');
                });

                describe('when new speed is available', function () {
                    beforeEach(function () {
                        state.setSpeed('0.75', true);
                    });

                    it('set new speed', function () {
                        expect(state.speed).toEqual('0.75');
                    });

                    it('save setting for new speed', function () {

                        expect(state.storage.getItem('general_speed')).toBe('0.75');
                        expect(state.storage.getItem('video_speed_' + state.id)).toBe('0.75');
                    });
                });

                describe('when new speed is not available', function () {
                    beforeEach(function () {
                        state.setSpeed('1.75');
                    });

                    it('set speed to 1.0x', function () {
                        expect(state.speed).toEqual('1.0');
                    });
                });

                it('check mapping', function () {
                    var map = {
                        '0.25': '0.75',
                        '0.50': '0.75',
                        '2.0': '1.50'
                    };

                    $.each(map, function(key, expected) {
                        state.setSpeed(key, true);
                        expect(state.speed).toBe(expected);
                    });
                });
            });
        });

        describe('getDuration', function () {
            beforeEach(function () {
                loadFixtures('video.html');
                state = new Video('#example');
            });

            it('return duration for current video', function () {
                expect(state.getDuration()).toEqual(400);
            });
        });

        describe('log', function () {
            beforeEach(function () {
                loadFixtures('video_html5.html');
                state = new Video('#example');
                spyOn(Logger, 'log');
                state.videoPlayer.log('someEvent', {
                    currentTime: 25,
                    speed: '1.0'
                });
            });

            it('call the logger with valid extra parameters', function () {
                expect(Logger.log).toHaveBeenCalledWith('someEvent', {
                    id: 'id',
                    code: 'html5',
                    currentTime: 25,
                    speed: '1.0'
                });
            });
        });
    });
}).call(this);
