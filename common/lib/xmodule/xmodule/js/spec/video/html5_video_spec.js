(function () {
    describe('Video HTML5Video', function () {
        var state, player, oldOTBD, playbackRates = [0.75, 1.0, 1.25, 1.5];

        function initialize() {
            loadFixtures('video_html5.html');
            state = new Video('#example');
            player = state.videoPlayer.player;
        }

        beforeEach(function () {
            oldOTBD = window.onTouchBasedDevice;
            window.onTouchBasedDevice = jasmine.createSpy('onTouchBasedDevice').andReturn(false);
            initialize();
            player.config.events.onReady = jasmine.createSpy('onReady');
        });

        afterEach(function() {
            YT.Player = void 0;
            $.fn.scrollTo.reset();
            $('.subtitles').remove();
            $('source').remove();
            window.onTouchBasedDevice = oldOTBD;
        });

        describe('events:', function () {
            beforeEach(function () {
                spyOn(player, 'callStateChangeCallback').andCallThrough();
            });

            describe('click', function () {
                describe('when player is paused', function () {
                    beforeEach(function () {
                        spyOn(player.video, 'play').andCallThrough();
                        player.playerState = STATUS.PAUSED;
                        $(player.videoEl).trigger('click');
                    });

                    it('native play event was called', function () {
                        expect(player.video.play).toHaveBeenCalled();
                    });

                    // Temporarily disabled due to intermittent failures
                    // Fails with "timeout: timed out after 1000 msec waiting for Player state should be changed"
                    // on Firefox
                    xit('player state was changed', function () {
                        waitsFor(function () {
                            return player.getPlayerState() !== STATUS.PAUSED;
                        }, 'Player state should be changed', WAIT_TIMEOUT);

                        runs(function () {
                            expect(player.getPlayerState()).toBe(STATUS.PLAYING);
                        });
                    });

                    it('callback was called', function () {
                        waitsFor(function () {
                            return state.videoPlayer.player.getPlayerState() !== STATUS.PAUSED;
                        }, 'Player state should be changed', WAIT_TIMEOUT);

                        runs(function () {
                            expect(player.callStateChangeCallback).toHaveBeenCalled();
                        });
                    });
                });
            });

            describe('when player is played', function () {
                beforeEach(function () {
                    spyOn(player.video, 'pause').andCallThrough();
                    player.playerState  = STATUS.PLAYING;
                    $(player.videoEl).trigger('click');
                });

                it('native event was called', function () {
                    expect(player.video.pause).toHaveBeenCalled();
                });

                it('player state was changed', function () {
                    waitsFor(function () {
                        return player.getPlayerState() !== STATUS.PLAYING;
                    }, 'Player state should be changed', WAIT_TIMEOUT);

                    runs(function () {
                        expect(player.getPlayerState()).toBe(STATUS.PAUSED);
                    });
                });

                it('callback was called', function () {
                    waitsFor(function () {
                        return player.getPlayerState() !== STATUS.PLAYING;
                    }, 'Player state should be changed', WAIT_TIMEOUT);

                    runs(function () {
                        expect(player.callStateChangeCallback).toHaveBeenCalled();
                    });
                });
            });

            describe('play', function () {
                beforeEach(function () {
                    spyOn(player.video, 'play').andCallThrough();
                    player.playerState = STATUS.PAUSED;
                    player.playVideo();
                });

                it('native event was called', function () {
                    expect(player.video.play).toHaveBeenCalled();
                });

                it('player state was changed', function () {
                    waitsFor(function () {
                        return player.getPlayerState() !== STATUS.PAUSED;
                    }, 'Player state should be changed', WAIT_TIMEOUT);

                    runs(function () {
                        expect(player.getPlayerState()).toBe(STATUS.PLAYING);
                    });
                });

                it('callback was called', function () {
                    waitsFor(function () {
                        return player.getPlayerState() !== STATUS.PAUSED;
                    }, 'Player state should be changed', WAIT_TIMEOUT);

                    runs(function () {
                        expect(player.callStateChangeCallback).toHaveBeenCalled();
                    });
                });
            });

            describe('pause', function () {
                beforeEach(function () {
                    spyOn(player.video, 'pause').andCallThrough();
                    player.playVideo();
                    player.pauseVideo();
                });

                it('native event was called', function () {
                    expect(player.video.pause).toHaveBeenCalled();
                });

                it('player state was changed', function () {
                    waitsFor(function () {
                        return player.getPlayerState() !== STATUS.UNSTARTED;
                    }, 'Player state should be changed', WAIT_TIMEOUT);

                    runs(function () {
                        expect(player.getPlayerState()).toBe(STATUS.PAUSED);
                    });
                });

                it('callback was called', function () {
                    waitsFor(function () {
                        return player.getPlayerState() !== STATUS.UNSTARTED;
                    }, 'Player state should be changed', WAIT_TIMEOUT);
                    runs(function () {
                        expect(player.callStateChangeCallback).toHaveBeenCalled();
                    });
                });
            });

            describe('canplay', function () {
                beforeEach(function () {
                    waitsFor(function () {
                        return player.getPlayerState() !== STATUS.UNSTARTED;
                    }, 'Video cannot be played', WAIT_TIMEOUT);
                });

                it('player state was changed', function () {
                    runs(function () {
                        expect(player.getPlayerState()).toBe(STATUS.PAUSED);
                    });
                });

                it('end property was defined', function () {
                    runs(function () {
                        expect(player.end).not.toBeNull();
                    });
                });

                it('start position was defined', function () {
                    runs(function () {
                        expect(player.video.currentTime).toBe(player.start);
                    });
                });

                it('onReady callback was called', function () {
                    runs(function () {
                        expect(player.config.events.onReady).toHaveBeenCalled();
                    });
                });
            });

            describe('ended', function () {
                beforeEach(function () {
                    waitsFor(function () {
                        return player.getPlayerState() !== STATUS.UNSTARTED;
                    }, 'Video cannot be played', WAIT_TIMEOUT);
                });

                it('player state was changed', function () {
                    runs(function () {
                        jasmine.fireEvent(player.video, 'ended');
                        expect(player.getPlayerState()).toBe(STATUS.ENDED);
                    });
                });

                it('callback was called', function () {
                    jasmine.fireEvent(player.video, 'ended');
                    expect(player.callStateChangeCallback).toHaveBeenCalled();
                });
            });
        });

        describe('methods', function () {
            var volume, seek, duration, playbackRate;

            beforeEach(function () {
                waitsFor(function () {
                    volume = player.video.volume;
                    seek = player.video.currentTime;
                    return player.playerState === STATUS.PAUSED;
                }, 'Video cannot be played', WAIT_TIMEOUT);
            });

            it('pauseVideo', function () {
                runs(function () {
                    spyOn(player.video, 'pause').andCallThrough();
                    player.pauseVideo();
                    expect(player.video.pause).toHaveBeenCalled();
                });
            });

            describe('seekTo', function () {
                it('set new correct value', function () {
                    runs(function () {
                        player.seekTo(2);
                        expect(player.getCurrentTime()).toBe(2);
                    });
                });

                it('set new inccorrect values', function () {
                    runs(function () {
                        player.seekTo(-50);
                        expect(player.getCurrentTime()).toBe(seek);
                        player.seekTo('5');
                        expect(player.getCurrentTime()).toBe(seek);
                        player.seekTo(500000);
                        expect(player.getCurrentTime()).toBe(seek);
                    });
                });
            });

            describe('setVolume', function () {
                it('set new correct value', function () {
                    runs(function () {
                        player.setVolume(50);
                        expect(player.getVolume()).toBe(50 * 0.01);
                    });
                });

                it('set new incorrect values', function () {
                    runs(function () {
                        player.setVolume(-50);
                        expect(player.getVolume()).toBe(volume);
                        player.setVolume('5');
                        expect(player.getVolume()).toBe(volume);
                        player.setVolume(500000);
                        expect(player.getVolume()).toBe(volume);
                    });
                });
            });

            it('getCurrentTime', function () {
                runs(function () {
                    player.video.currentTime = 3;
                    expect(player.getCurrentTime()).toBe(player.video.currentTime);
                });
            });

            it('playVideo', function () {
                runs(function () {
                    spyOn(player.video, 'play').andCallThrough();
                    player.playVideo();
                    expect(player.video.play).toHaveBeenCalled();
                });
            });

            it('getPlayerState', function () {
                runs(function () {
                    player.playerState = STATUS.PLAYING;
                    expect(player.getPlayerState()).toBe(STATUS.PLAYING);
                    player.playerState = STATUS.ENDED;
                    expect(player.getPlayerState()).toBe(STATUS.ENDED);
                });
            });

            it('getVolume', function () {
                runs(function () {
                    volume = player.video.volume = 0.5;
                    expect(player.getVolume()).toBe(volume);
                });
            });

            it('getDuration', function () {
                runs(function () {
                    duration = player.video.duration;
                    expect(player.getDuration()).toBe(duration);
                });
            });

            describe('setPlaybackRate', function () {
                it('set a correct value', function () {
                    playbackRate = 1.5;
                    player.setPlaybackRate(playbackRate);
                    expect(player.video.playbackRate).toBe(playbackRate);
                });

                it('set NaN value', function () {
                    var oldPlaybackRate = player.video.playbackRate;

                    // When we try setting the playback rate to some
                    // non-numerical value, nothing should happen.
                    playbackRate = NaN;
                    player.setPlaybackRate(playbackRate);
                    expect(player.video.playbackRate).toBe(oldPlaybackRate);
                });
            });

            it('getAvailablePlaybackRates', function () {
                expect(player.getAvailablePlaybackRates()).toEqual(playbackRates);
            });
        });
    });
}).call(this);
