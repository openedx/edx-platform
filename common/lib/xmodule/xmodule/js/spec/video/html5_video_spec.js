(function(undefined) {
    describe('Video HTML5Video', function() {
        var STATUS = window.STATUS;
        var state,
            oldOTBD,
            playbackRates = [0.75, 1.0, 1.25, 1.5],
            describeInfo,
            POSTER_URL = '/media/video-images/poster.png';

        beforeEach(function() {
            oldOTBD = window.onTouchBasedDevice;
            window.onTouchBasedDevice = jasmine
                .createSpy('onTouchBasedDevice').and.returnValue(null);

            state = jasmine.initializePlayer('video_html5.html');
        });

        afterEach(function() {
            state.storage.clear();
            state.videoPlayer.destroy();
            $.fn.scrollTo.calls.reset();
            $('source').remove();
            window.onTouchBasedDevice = oldOTBD;
        });

        describeInfo = new jasmine.DescribeInfo('on non-Touch devices ', function() {
            beforeEach(function() {
                state.videoPlayer.player.config.events.onReady = jasmine.createSpy('onReady');
            });

            describe('events:', function() {
                beforeEach(function() {
                    spyOn(state.videoPlayer.player, 'callStateChangeCallback').and.callThrough();
                });

                describe('[click]', function() {
                    describe('when player is paused', function() {
                        beforeEach(function() {
                            spyOn(state.videoPlayer.player.video, 'play').and.callThrough();
                            state.videoPlayer.player.playerState = STATUS.PAUSED;
                            $(state.videoPlayer.player.videoEl).trigger('click');
                        });

                        it('native play event was called', function() {
                            expect(state.videoPlayer.player.video.play).toHaveBeenCalled();
                        });

                        it('player state was changed', function(done) {
                            jasmine.waitUntil(function() {
                                return state.videoPlayer.player.getPlayerState() === STATUS.PLAYING;
                            }).always(done);
                        });
                    });

                    describe('[player is playing]', function() {
                        beforeEach(function() {
                            spyOn(state.videoPlayer.player.video, 'pause').and.callThrough();
                            state.videoPlayer.player.playerState = STATUS.PLAYING;
                            $(state.videoPlayer.player.videoEl).trigger('click');
                        });

                        it('native event was called', function() {
                            expect(state.videoPlayer.player.video.pause).toHaveBeenCalled();
                        });

                        it('player state was changed', function(done) {
                            jasmine.waitUntil(function() {
                                return state.videoPlayer.player.getPlayerState() !== STATUS.PLAYING;
                            }).then(function() {
                                expect(state.videoPlayer.player.getPlayerState())
                                    .toBe(STATUS.PAUSED);
                            }).always(done);
                        });

                        it('callback was not called', function(done) {
                            jasmine.waitUntil(function() {
                                return state.videoPlayer.player.getPlayerState() !== STATUS.PLAYING;
                            }).then(function() {
                                expect(state.videoPlayer.player.callStateChangeCallback)
                                    .not.toHaveBeenCalled();
                            }).always(done);
                        });
                    });
                });

                describe('[play]', function() {
                    beforeEach(function() {
                        spyOn(state.videoPlayer.player.video, 'play').and.callThrough();
                        state.videoPlayer.player.playerState = STATUS.PAUSED;
                        state.videoPlayer.player.playVideo();
                    });

                    it('native event was called', function() {
                        expect(state.videoPlayer.player.video.play).toHaveBeenCalled();
                    });


                    it('player state was changed', function(done) {
                        jasmine.waitUntil(function() {
                            return state.videoPlayer.player.getPlayerState() !== STATUS.PAUSED;
                        }).then(function() {
                            expect([STATUS.BUFFERING, STATUS.PLAYING]).toContain(
                                state.videoPlayer.player.getPlayerState()
                            );
                        }).always(done);
                    });

                    it('callback was called', function(done) {
                        jasmine.waitUntil(function() {
                            return state.videoPlayer.player.getPlayerState() !== STATUS.PAUSED;
                        }).then(function() {
                            expect(state.videoPlayer.player.callStateChangeCallback)
                                .toHaveBeenCalled();
                        }).always(done);
                    });
                });

                describe('[pause]', function() {
                    beforeEach(function(done) {
                        spyOn(state.videoPlayer.player.video, 'pause').and.callThrough();
                        state.videoPlayer.player.playerState = STATUS.UNSTARTED;
                        state.videoPlayer.player.playVideo();

                        jasmine.waitUntil(function() {
                            return state.videoPlayer.player.getPlayerState() !== STATUS.UNSTARTED;
                        }).done(done);

                        state.videoPlayer.player.pauseVideo();
                    });

                    it('native event was called', function() {
                        expect(state.videoPlayer.player.video.pause).toHaveBeenCalled();
                    });

                    it('player state was changed', function(done) {
                        jasmine.waitUntil(function() {
                            return state.videoPlayer.player.getPlayerState() !== STATUS.PLAYING;
                        }).then(function() {
                            expect(state.videoPlayer.player.getPlayerState())
                                .toBe(STATUS.PAUSED);
                        }).always(done);
                    });

                    it('callback was called', function(done) {
                        jasmine.waitUntil(function() {
                            return state.videoPlayer.player.getPlayerState() !== STATUS.PLAYING;
                        }).then(function() {
                            expect(state.videoPlayer.player.callStateChangeCallback)
                                .toHaveBeenCalled();
                        }).always(done);
                    });
                });

                describe('[loadedmetadata]', function() {
                    it(
                        'player state was changed, start/end was defined, ' +
                        'onReady called', function(done) {
                        jasmine.fireEvent(state.videoPlayer.player.video, 'loadedmetadata');
                        jasmine.waitUntil(function() {
                            return state.videoPlayer.player.getPlayerState() !== STATUS.UNSTARTED;
                        }).then(function() {
                            expect(state.videoPlayer.player.getPlayerState())
                                .toBe(STATUS.PAUSED);
                            expect(state.videoPlayer.player.video.currentTime).toBe(0);
                            expect(state.videoPlayer.player.config.events.onReady)
                                .toHaveBeenCalled();
                        }).always(done);
                    });
                });

                describe('[ended]', function() {
                    beforeEach(function(done) {
                        state.videoPlayer.player.playVideo();
                        jasmine.waitUntil(function() {
                            return state.videoPlayer.player.getPlayerState() !== STATUS.UNSTARTED;
                        }).done(done);
                    });

                    it('player state was changed', function() {
                        jasmine.fireEvent(state.videoPlayer.player.video, 'ended');
                        expect(state.videoPlayer.player.getPlayerState()).toBe(STATUS.ENDED);
                    });

                    it('callback was called', function() {
                        jasmine.fireEvent(state.videoPlayer.player.video, 'ended');
                        expect(state.videoPlayer.player.callStateChangeCallback)
                            .toHaveBeenCalled();
                    });
                });
            });

            describe('methods', function() {
                var volume, seek, duration, playbackRate;

                beforeEach(function() {
                    volume = state.videoPlayer.player.video.volume;
                });

                it('pauseVideo', function() {
                    spyOn(state.videoPlayer.player.video, 'pause').and.callThrough();
                    state.videoPlayer.player.pauseVideo();
                    expect(state.videoPlayer.player.video.pause).toHaveBeenCalled();
                });

                describe('seekTo', function() {
                    it('set new correct value', function(done) {
                        state.videoPlayer.player.playVideo();
                        jasmine.waitUntil(function() {
                            return state.videoPlayer.player.getPlayerState() === STATUS.PLAYING;
                        }).then(function() {
                            state.videoPlayer.player.seekTo(2);
                            expect(state.videoPlayer.player.getCurrentTime()).toBe(2);
                        }).done(done);
                    });

                    it('set new incorrect values', function() {
                        var seek = state.videoPlayer.player.video.currentTime;
                        state.videoPlayer.player.seekTo(-50);
                        expect(state.videoPlayer.player.getCurrentTime()).toBe(seek);
                        state.videoPlayer.player.seekTo('5');
                        expect(state.videoPlayer.player.getCurrentTime()).toBe(seek);
                        state.videoPlayer.player.seekTo(500000);
                        expect(state.videoPlayer.player.getCurrentTime()).toBe(seek);
                    });
                });

                describe('setVolume', function() {
                    it('set new correct value', function() {
                        state.videoPlayer.player.setVolume(50);
                        expect(state.videoPlayer.player.getVolume()).toBe(50 * 0.01);
                    });

                    it('set new incorrect values', function() {
                        state.videoPlayer.player.setVolume(-50);
                        expect(state.videoPlayer.player.getVolume()).toBe(volume);
                        state.videoPlayer.player.setVolume('5');
                        expect(state.videoPlayer.player.getVolume()).toBe(volume);
                        state.videoPlayer.player.setVolume(500000);
                        expect(state.videoPlayer.player.getVolume()).toBe(volume);
                    });
                });

                it('getCurrentTime', function(done) {
                    state.videoPlayer.player.playVideo();
                    jasmine.waitUntil(function() {
                        return state.videoPlayer.player.getPlayerState() === STATUS.PLAYING;
                    }).then(function() {
                        state.videoPlayer.player.video.currentTime = 3;
                        expect(state.videoPlayer.player.getCurrentTime())
                            .toBe(state.videoPlayer.player.video.currentTime);
                    }).done(done);
                });

                it('playVideo', function() {
                    spyOn(state.videoPlayer.player.video, 'play').and.callThrough();
                    state.videoPlayer.player.playVideo();
                    expect(state.videoPlayer.player.video.play).toHaveBeenCalled();
                });

                it('getPlayerState', function() {
                    state.videoPlayer.player.playerState = STATUS.PLAYING;
                    expect(state.videoPlayer.player.getPlayerState()).toBe(STATUS.PLAYING);
                    state.videoPlayer.player.playerState = STATUS.ENDED;
                    expect(state.videoPlayer.player.getPlayerState()).toBe(STATUS.ENDED);
                });

                it('getVolume', function() {
                    volume = state.videoPlayer.player.video.volume = 0.5;
                    expect(state.videoPlayer.player.getVolume()).toBe(volume);
                });

                it('getDuration', function(done) {
                    state.videoPlayer.player.playVideo();
                    jasmine.waitUntil(function() {
                        return state.videoPlayer.player.getPlayerState() === STATUS.PLAYING;
                    }).then(function() {
                        duration = state.videoPlayer.player.video.duration;
                        expect(state.videoPlayer.player.getDuration()).toBe(duration);
                    }).always(done);
                });

                describe('setPlaybackRate', function() {
                    it('set a correct value', function() {
                        playbackRate = 1.5;
                        state.videoPlayer.player.setPlaybackRate(playbackRate);
                        expect(state.videoPlayer.player.video.playbackRate).toBe(playbackRate);
                    });

                    it('set NaN value', function() {
                        var oldPlaybackRate = state.videoPlayer.player.video.playbackRate;

                        // When we try setting the playback rate to some
                        // non-numerical value, nothing should happen.
                        playbackRate = NaN;
                        state.videoPlayer.player.setPlaybackRate(playbackRate);
                        expect(state.videoPlayer.player.video.playbackRate)
                            .toBe(oldPlaybackRate);
                    });
                });

                it('getAvailablePlaybackRates', function() {
                    expect(state.videoPlayer.player.getAvailablePlaybackRates())
                        .toEqual(playbackRates);
                });

                it('_getLogs', function(done) {
                    state.videoPlayer.player.playVideo();
                    jasmine.waitUntil(function() {
                        return state.videoPlayer.player.getPlayerState() === STATUS.PLAYING;
                    }).then(function() {
                        var logs = state.videoPlayer.player._getLogs();
                        expect(logs).toEqual(jasmine.any(Array));
                        expect(logs.length).toBeGreaterThan(0);
                    }).done(done);
                });
            });

            describe('poster', function() {
                it('has url in player config', function() {
                    expect(state.videoPlayer.player.config.poster).toEqual(POSTER_URL);
                    expect(state.videoPlayer.player.videoEl).toHaveAttrs({
                        poster: POSTER_URL
                    });
                });
            });
        });

        describe('non-hls encoding', function() {
            beforeEach(function(done) {
                state = jasmine.initializePlayer('video_html5.html');
                done();
            });
            jasmine.getEnv().describe(describeInfo.description, describeInfo.specDefinitions);
        });

        describe('hls encoding', function() {
            beforeEach(function(done) {
                state = jasmine.initializeHLSPlayer();
                done();
            });
            jasmine.getEnv().describe(describeInfo.description, describeInfo.specDefinitions);
        });

        it('does not show poster for html5 video if url is not present', function() {
            state = jasmine.initializePlayer(
                'video_html5.html',
                {
                    poster: null
                }
            );
            expect(state.videoPlayer.player.config.poster).toEqual(null);
            expect(state.videoPlayer.player.videoEl).not.toHaveAttr('poster');
        });

        it('does not show poster for hls video if url is not present', function() {
            state = jasmine.initializePlayer(
                'video_hls.html',
                {
                    poster: null
                }
            );
            expect(state.videoPlayer.player.config.poster).toEqual(null);
            expect(state.videoPlayer.player.videoEl).not.toHaveAttr('poster');
        });

        it('native controls are used on  iPhone', function() {
            window.onTouchBasedDevice.and.returnValue(['iPhone']);

            state = jasmine.initializePlayer('video_html5.html');

            state.videoPlayer.player.config.events.onReady = jasmine.createSpy('onReady');

            expect($('video')).toHaveAttr('controls');
        });
    });
}).call(this);
