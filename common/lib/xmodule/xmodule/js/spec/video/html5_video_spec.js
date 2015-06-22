(function (undefined) {
    describe('Video HTML5Video', function () {
        var state, oldOTBD, playbackRates = [0.75, 1.0, 1.25, 1.5];

        beforeEach(function () {
            oldOTBD = window.onTouchBasedDevice;
            window.onTouchBasedDevice = jasmine
                .createSpy('onTouchBasedDevice').andReturn(null);
        });

        afterEach(function () {
            state.storage.clear();
            state.videoPlayer.destroy();
            $.fn.scrollTo.reset();
            $('source').remove();
            window.onTouchBasedDevice = oldOTBD;
        });

        describe('on non-Touch devices', function () {
            beforeEach(function () {
                state = jasmine.initializePlayer('video_html5.html');

                state.videoPlayer.player.config.events.onReady = jasmine.createSpy('onReady');
            });

            describe('events:', function () {
                beforeEach(function () {
                    spyOn(state.videoPlayer.player, 'callStateChangeCallback').andCallThrough();
                });

                describe('[click]', function () {
                    describe('when player is paused', function () {
                        beforeEach(function () {
                            spyOn(state.videoPlayer.player.video, 'play').andCallThrough();
                            state.videoPlayer.player.playerState = STATUS.PAUSED;
                            $(state.videoPlayer.player.videoEl).trigger('click');
                        });

                        it('native play event was called', function () {
                            expect(state.videoPlayer.player.video.play).toHaveBeenCalled();
                        });

                        it('player state was changed', function () {
                            waitsFor(function () {
                                return state.videoPlayer.player.getPlayerState() !== STATUS.PAUSED;
                            }, 'Player state should be changed', WAIT_TIMEOUT);

                            runs(function () {
                                expect(state.videoPlayer.player.getPlayerState())
                                    .toBe(STATUS.PLAYING);
                            });
                        });

                        it('callback was not called', function () {
                            waitsFor(function () {
                                return state.videoPlayer.player.getPlayerState() !== STATUS.PAUSED;
                            }, 'Player state should be changed', WAIT_TIMEOUT);

                            runs(function () {
                                expect(state.videoPlayer.player.callStateChangeCallback)
                                    .not.toHaveBeenCalled();
                            });
                        });
                    });

                    describe('[player is playing]', function () {
                        beforeEach(function () {
                            spyOn(state.videoPlayer.player.video, 'pause').andCallThrough();
                            state.videoPlayer.player.playerState  = STATUS.PLAYING;
                            $(state.videoPlayer.player.videoEl).trigger('click');
                        });

                        it('native event was called', function () {
                            expect(state.videoPlayer.player.video.pause).toHaveBeenCalled();
                        });

                        it('player state was changed', function () {
                            waitsFor(function () {
                                return state.videoPlayer.player.getPlayerState() !== STATUS.PLAYING;
                            }, 'Player state should be changed', WAIT_TIMEOUT);

                            runs(function () {
                                expect(state.videoPlayer.player.getPlayerState())
                                    .toBe(STATUS.PAUSED);
                            });
                        });

                        it('callback was not called', function () {
                            waitsFor(function () {
                                return state.videoPlayer.player.getPlayerState() !== STATUS.PLAYING;
                            }, 'Player state should be changed', WAIT_TIMEOUT);

                            runs(function () {
                                expect(state.videoPlayer.player.callStateChangeCallback)
                                    .not.toHaveBeenCalled();
                            });
                        });
                    });
                });

                describe('[play]', function () {
                    beforeEach(function () {
                        spyOn(state.videoPlayer.player.video, 'play').andCallThrough();
                        state.videoPlayer.player.playerState = STATUS.PAUSED;
                        state.videoPlayer.player.playVideo();
                    });

                    it('native event was called', function () {
                        expect(state.videoPlayer.player.video.play).toHaveBeenCalled();
                    });


                    it('player state was changed', function () {
                        waitsFor(function () {
                            return state.videoPlayer.player.getPlayerState() !== STATUS.PAUSED;
                        }, 'Player state should be changed', WAIT_TIMEOUT);

                        runs(function () {
                            expect(state.videoPlayer.player.getPlayerState())
                                .toBe(STATUS.BUFFERING);
                        });
                    });

                    it('callback was called', function () {
                        waitsFor(function () {
                            return state.videoPlayer.player.getPlayerState() !== STATUS.PAUSED;
                        }, 'Player state should be changed', WAIT_TIMEOUT);

                        runs(function () {
                            expect(state.videoPlayer.player.callStateChangeCallback)
                                .toHaveBeenCalled();
                        });
                    });
                });

                describe('[pause]', function () {
                    beforeEach(function () {
                        spyOn(state.videoPlayer.player.video, 'pause').andCallThrough();
                        state.videoPlayer.player.playerState = STATUS.UNSTARTED;
                        state.videoPlayer.player.playVideo();
                        waitsFor(function () {
                            return state.videoPlayer.player.getPlayerState() !== STATUS.UNSTARTED;
                        }, 'Video never started playing', WAIT_TIMEOUT);
                        state.videoPlayer.player.pauseVideo();
                    });

                    it('native event was called', function () {
                        expect(state.videoPlayer.player.video.pause).toHaveBeenCalled();
                    });

                    it('player state was changed', function () {
                        waitsFor(function () {
                            return state.videoPlayer.player.getPlayerState() !== STATUS.PLAYING;
                        }, 'Player state should be changed', WAIT_TIMEOUT);

                        runs(function () {
                            expect(state.videoPlayer.player.getPlayerState())
                                .toBe(STATUS.PAUSED);
                        });
                    });

                    it('callback was called', function () {
                        waitsFor(function () {
                            return state.videoPlayer.player.getPlayerState() !== STATUS.PLAYING;
                        }, 'Player state should be changed', WAIT_TIMEOUT);
                        runs(function () {
                            expect(state.videoPlayer.player.callStateChangeCallback)
                                .toHaveBeenCalled();
                        });
                    });
                });

                describe('[loadedmetadata]', function () {
                    it(
                        'player state was changed, start/end was defined, ' +
                        'onReady called', function ()
                    {
                        waitsFor(function () {
                            return state.videoPlayer.player.getPlayerState() !== STATUS.UNSTARTED;
                        }, 'Video cannot be played', WAIT_TIMEOUT);

                        runs(function () {
                            expect(state.videoPlayer.player.getPlayerState())
                                .toBe(STATUS.PAUSED);
                            expect(state.videoPlayer.player.video.currentTime).toBe(0);
                            expect(state.videoPlayer.player.config.events.onReady)
                                .toHaveBeenCalled();
                        });
                    });
                });

                describe('[ended]', function () {
                    beforeEach(function () {
                        waitsFor(function () {
                            return state.videoPlayer.player.getPlayerState() !== STATUS.UNSTARTED;
                        }, 'Video cannot be played', WAIT_TIMEOUT);
                    });

                    it('player state was changed', function () {
                        runs(function () {
                            jasmine.fireEvent(state.videoPlayer.player.video, 'ended');
                            expect(state.videoPlayer.player.getPlayerState()).toBe(STATUS.ENDED);
                        });
                    });

                    it('callback was called', function () {
                        jasmine.fireEvent(state.videoPlayer.player.video, 'ended');
                        expect(state.videoPlayer.player.callStateChangeCallback)
                            .toHaveBeenCalled();
                    });
                });
            });

            describe('methods', function () {
                var volume, seek, duration, playbackRate;

                beforeEach(function () {
                    waitsFor(function () {
                        volume = state.videoPlayer.player.video.volume;
                        seek = state.videoPlayer.player.video.currentTime;
                        return state.videoPlayer.player.playerState === STATUS.PAUSED;
                    }, 'Video cannot be played', WAIT_TIMEOUT);
                });

                it('pauseVideo', function () {
                    runs(function () {
                        spyOn(state.videoPlayer.player.video, 'pause').andCallThrough();
                        state.videoPlayer.player.pauseVideo();
                        expect(state.videoPlayer.player.video.pause).toHaveBeenCalled();
                    });
                });

                describe('seekTo', function () {
                    it('set new correct value', function () {
                        runs(function () {
                            state.videoPlayer.player.seekTo(2);
                            expect(state.videoPlayer.player.getCurrentTime()).toBe(2);
                        });
                    });

                    it('set new inccorrect values', function () {
                        runs(function () {
                            state.videoPlayer.player.seekTo(-50);
                            expect(state.videoPlayer.player.getCurrentTime()).toBe(seek);
                            state.videoPlayer.player.seekTo('5');
                            expect(state.videoPlayer.player.getCurrentTime()).toBe(seek);
                            state.videoPlayer.player.seekTo(500000);
                            expect(state.videoPlayer.player.getCurrentTime()).toBe(seek);
                        });
                    });
                });

                describe('setVolume', function () {
                    it('set new correct value', function () {
                        runs(function () {
                            state.videoPlayer.player.setVolume(50);
                            expect(state.videoPlayer.player.getVolume()).toBe(50 * 0.01);
                        });
                    });

                    it('set new incorrect values', function () {
                        runs(function () {
                            state.videoPlayer.player.setVolume(-50);
                            expect(state.videoPlayer.player.getVolume()).toBe(volume);
                            state.videoPlayer.player.setVolume('5');
                            expect(state.videoPlayer.player.getVolume()).toBe(volume);
                            state.videoPlayer.player.setVolume(500000);
                            expect(state.videoPlayer.player.getVolume()).toBe(volume);
                        });
                    });
                });

                it('getCurrentTime', function () {
                    runs(function () {
                        state.videoPlayer.player.video.currentTime = 3;
                        expect(state.videoPlayer.player.getCurrentTime())
                            .toBe(state.videoPlayer.player.video.currentTime);
                    });
                });

                it('playVideo', function () {
                    runs(function () {
                        spyOn(state.videoPlayer.player.video, 'play').andCallThrough();
                        state.videoPlayer.player.playVideo();
                        expect(state.videoPlayer.player.video.play).toHaveBeenCalled();
                    });
                });

                it('getPlayerState', function () {
                    runs(function () {
                        state.videoPlayer.player.playerState = STATUS.PLAYING;
                        expect(state.videoPlayer.player.getPlayerState()).toBe(STATUS.PLAYING);
                        state.videoPlayer.player.playerState = STATUS.ENDED;
                        expect(state.videoPlayer.player.getPlayerState()).toBe(STATUS.ENDED);
                    });
                });

                it('getVolume', function () {
                    runs(function () {
                        volume = state.videoPlayer.player.video.volume = 0.5;
                        expect(state.videoPlayer.player.getVolume()).toBe(volume);
                    });
                });

                it('getDuration', function () {
                    runs(function () {
                        duration = state.videoPlayer.player.video.duration;
                        expect(state.videoPlayer.player.getDuration()).toBe(duration);
                    });
                });

                describe('setPlaybackRate', function () {
                    it('set a correct value', function () {
                        playbackRate = 1.5;
                        state.videoPlayer.player.setPlaybackRate(playbackRate);
                        expect(state.videoPlayer.player.video.playbackRate).toBe(playbackRate);
                    });

                    it('set NaN value', function () {
                        var oldPlaybackRate = state.videoPlayer.player.video.playbackRate;

                        // When we try setting the playback rate to some
                        // non-numerical value, nothing should happen.
                        playbackRate = NaN;
                        state.videoPlayer.player.setPlaybackRate(playbackRate);
                        expect(state.videoPlayer.player.video.playbackRate)
                            .toBe(oldPlaybackRate);
                    });
                });

                it('getAvailablePlaybackRates', function () {
                    expect(state.videoPlayer.player.getAvailablePlaybackRates())
                        .toEqual(playbackRates);
                });

                it('_getLogs', function () {
                    runs(function () {
                        var logs = state.videoPlayer.player._getLogs();
                        expect(logs).toEqual(jasmine.any(Array));
                        expect(logs.length).toBeGreaterThan(0);
                    });
                });
            });
        });

        it('native controls are used on  iPhone', function () {
            window.onTouchBasedDevice.andReturn(['iPhone']);

            state = jasmine.initializePlayer('video_html5.html');

            state.videoPlayer.player.config.events.onReady = jasmine.createSpy('onReady');

            expect($('video')).toHaveAttr('controls');
        });
    });
}).call(this);
