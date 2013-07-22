(function () {
    describe('VideoAlpha', function () {
        var oldOTBD;

        beforeEach(function () {
            jasmine.stubRequests();
            oldOTBD = window.onTouchBasedDevice;
            window.onTouchBasedDevice = jasmine.createSpy('onTouchBasedDevice').andReturn(false);
            this.videosDefinition = '0.75:slowerSpeedYoutubeId,1.0:normalSpeedYoutubeId';
            this.slowerSpeedYoutubeId = 'slowerSpeedYoutubeId';
            this.normalSpeedYoutubeId = 'normalSpeedYoutubeId';
        });

        afterEach(function () {
            window.OldVideoPlayerAlpha = undefined;
            window.onYouTubePlayerAPIReady = undefined;
            window.onHTML5PlayerAPIReady = undefined;
            $('source').remove();
            window.onTouchBasedDevice = oldOTBD;
        });

        describe('constructor', function () {
            describe('YT', function () {
                beforeEach(function () {
                    loadFixtures('videoalpha.html');
                    $.cookie.andReturn('0.75');
                });

                describe('by default', function () {
                    beforeEach(function () {
                        this.state = new window.VideoAlpha('#example');
                    });

                    it('check videoType', function () {
                        expect(this.state.videoType).toEqual('youtube');
                    });

                    it('reset the current video player', function () {
                        expect(window.OldVideoPlayerAlpha).toBeUndefined();
                    });

                    it('set the elements', function () {
                        expect(this.state.el).toBe('#video_id');
                    });

                    it('parse the videos', function () {
                        expect(this.state.videos).toEqual({
                            '0.75': this.slowerSpeedYoutubeId,
                            '1.0': this.normalSpeedYoutubeId
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
                    loadFixtures('videoalpha_html5.html');
                    this.stubVideoPlayerAlpha = jasmine.createSpy('VideoPlayerAlpha');
                    $.cookie.andReturn('0.75');
                });

                describe('by default', function () {
                    beforeEach(function () {
                        state = new window.VideoAlpha('#example');
                    });

                    afterEach(function () {
                        state = undefined;
                    });

                    it('check videoType', function () {
                        expect(state.videoType).toEqual('html5');
                    });

                    it('reset the current video player', function () {
                        expect(window.OldVideoPlayerAlpha).toBeUndefined();
                    });

                    it('set the elements', function () {
                        expect(state.el).toBe('#video_id');
                    });

                    it('parse the videos if subtitles exist', function () {
                        var sub = 'test_name_of_the_subtitles';

                        expect(state.videos).toEqual({
                            '0.75': sub,
                            '1.0': sub,
                            '1.25': sub,
                            '1.5': sub
                        });
                    });

                    it('parse the videos if subtitles do not exist', function () {
                        var sub = '';

                        $('#example').find('.videoalpha').data('sub', '');
                        state = new window.VideoAlpha('#example');

                        expect(state.videos).toEqual({
                            '0.75': sub,
                            '1.0': sub,
                            '1.25': sub,
                            '1.5': sub
                        });
                    });

                    it('parse Html5 sources', function () {
                        var html5Sources = {
                            mp4: 'test.mp4',
                            webm: 'test.webm',
                            ogg: 'test.ogv'
                        };

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
                        state = new VideoAlpha('#example');
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
                loadFixtures('videoalpha.html');
                $.cookie.andReturn('1.0');
                state = new VideoAlpha('#example');
            });

            describe('with speed', function () {
                it('return the video id for given speed', function () {
                    expect(state.youtubeId('0.75')).toEqual(this.slowerSpeedYoutubeId);
                    expect(state.youtubeId('1.0')).toEqual(this.normalSpeedYoutubeId);
                });
            });

            describe('without speed', function () {
                it('return the video id for current speed', function () {
                    expect(state.youtubeId()).toEqual(this.normalSpeedYoutubeId);
                });
            });
        });

        describe('setSpeed', function () {
            describe('YT', function () {
                beforeEach(function () {
                    loadFixtures('videoalpha.html');
                    state = new VideoAlpha('#example');
                });

                describe('when new speed is available', function () {
                    beforeEach(function () {
                        state.setSpeed('0.75');
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
                    loadFixtures('videoalpha_html5.html');
                    state = new VideoAlpha('#example');
                });

                describe('when new speed is available', function () {
                    beforeEach(function () {
                        state.setSpeed('0.75');
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
                loadFixtures('videoalpha.html');
                state = new VideoAlpha('#example');
            });

            it('return duration for current video', function () {
                expect(state.getDuration()).toEqual(200);
            });
        });

        describe('log', function () {
            beforeEach(function () {
                loadFixtures('videoalpha_html5.html');
                state = new VideoAlpha('#example');
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
