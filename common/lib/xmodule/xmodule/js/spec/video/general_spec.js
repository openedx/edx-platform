(function () {
    describe('Video', function () {
        var oldOTBD;

        beforeEach(function () {
            jasmine.stubRequests();
            this.videosDefinition = '0.75:7tqY6eQzVhE,1.0:cogebirgzzM';
            this['7tqY6eQzVhE'] = '7tqY6eQzVhE';
            this['cogebirgzzM'] = 'cogebirgzzM';
        });

        afterEach(function () {
            window.OldVideoPlayer = undefined;
            window.onYouTubePlayerAPIReady = undefined;
            window.onHTML5PlayerAPIReady = undefined;
            $('source').remove();
        });

        describe('constructor', function () {
            describe('YT', function () {
                beforeEach(function () {
                    loadFixtures('video.html');
                    $.cookie.andReturn('0.75');
                });

                describe('by default', function () {
                    beforeEach(function () {
                        this.state = new window.Video('#example');
                    });

                    it('check videoType', function () {
                        expect(this.state.videoType).toEqual('youtube');
                    });

                    it('reset the current video player', function () {
                        expect(window.OldVideoPlayer).toBeUndefined();
                    });

                    it('set the elements', function () {
                        expect(this.state.el).toBe('#video_id');
                    });

                    it('parse the videos', function () {
                        expect(this.state.videos).toEqual({
                            '0.75': this['7tqY6eQzVhE'],
                            '1.0': this['cogebirgzzM']
                        });
                    });

                    it('parse available video speeds', function () {
                        expect(this.state.speeds).toEqual(['0.75', '1.0']);
                    });

                    it('set current video speed via cookie', function () {
                        expect(this.state.speed).toEqual('0.75');
                    });
                });
            });

            describe('HTML5', function () {
                var state;

                beforeEach(function () {
                    loadFixtures('video_html5.html');
                    this.stubVideoPlayer = jasmine.createSpy('VideoPlayer');
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

                    it('reset the current video player', function () {
                        expect(window.OldVideoPlayer).toBeUndefined();
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
                            '1.5': sub
                        });
                    });

                    it('parse the videos if subtitles do not exist', function () {
                        var sub = '';

                        $('#example').find('.video').data('sub', '');
                        state = new window.Video('#example');

                        expect(state.videos).toEqual({
                            '0.75': sub,
                            '1.0': sub,
                            '1.25': sub,
                            '1.5': sub
                        });
                    });

                    it('parse Html5 sources', function () {
                        var html5Sources = {
                                mp4: null,
                                webm: null,
                                ogg: null
                            }, v = document.createElement('video');

                        if (!!(v.canPlayType && v.canPlayType('video/webm; codecs="vp8, vorbis"').replace(/no/, ''))) {
                            html5Sources['webm'] = 'xmodule/include/fixtures/test.webm';
                        }

                        if (!!(v.canPlayType && v.canPlayType('video/mp4; codecs="avc1.42E01E, mp4a.40.2"').replace(/no/, ''))) {
                            html5Sources['mp4'] = 'xmodule/include/fixtures/test.mp4';
                        }

                        if (!!(v.canPlayType && v.canPlayType('video/ogg; codecs="theora"').replace(/no/, ''))) {
                            html5Sources['ogg'] = 'xmodule/include/fixtures/test.ogv';
                        }

                        expect(state.html5Sources).toEqual(html5Sources);
                    });

                    it('parse available video speeds', function () {
                        var speeds = jasmine.stubbedHtml5Speeds;

                        expect(state.speeds).toEqual(speeds);
                    });

                    it('set current video speed via cookie', function () {
                        expect(state.speed).toEqual('0.75');
                    });
                });

                // Note that the loading of stand alone HTML5 player API is handled by
                // Require JS. When state.videoPlayer is created, the stand alone HTML5
                // player object is already loaded, so no further testing in that case
                // is required.
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
                    expect(state.youtubeId('0.75')).toEqual(this['7tqY6eQzVhE']);
                    expect(state.youtubeId('1.0')).toEqual(this['cogebirgzzM']);
                });
            });

            describe('without speed', function () {
                it('return the video id for current speed', function () {
                    expect(state.youtubeId()).toEqual(this.cogebirgzzM);
                });
            });
        });

        describe('multiple YT on page', function () {
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

            it('check for YT availability is performed only once', function () {
                var numAjaxCalls = 0;

                // Total ajax calls made.
                numAjaxCalls = $.ajax.calls.length;

                // Subtract ajax calls to get captions.
                numAjaxCalls -= $.ajaxWithPrefix.calls.length;

                // Subtract ajax calls to get metadata for each video.
                numAjaxCalls -= 3;

                // This should leave just one call. It was made to check
                // for YT availability.
                expect(numAjaxCalls).toBe(1);
            });
        });

        describe('setSpeed', function () {
            describe('YT', function () {
                beforeEach(function () {
                    loadFixtures('video.html');
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
                        expect($.cookie).toHaveBeenCalledWith('video_speed', '0.75', {
                            expires: 3650,
                            path: '/'
                        });
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
                        expect($.cookie).toHaveBeenCalledWith('video_speed', '0.75', {
                            expires: 3650,
                            path: '/'
                        });
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
            });
        });

        describe('getDuration', function () {
            beforeEach(function () {
                loadFixtures('video.html');
                state = new Video('#example');
            });

            it('return duration for current video', function () {
                expect(state.getDuration()).toEqual(200);
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
