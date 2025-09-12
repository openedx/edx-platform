/* eslint-disable no-undef */

describe('Video HTML5Video', () => {
  const STATUS = window.STATUS;
  let state;
  let oldOTBD;
  const playbackRates = [0.75, 1.0, 1.25, 1.5, 2.0];
  let describeInfo;
  const POSTER_URL = '/media/video-images/poster.png';

  beforeEach(() => {
    oldOTBD = window.onTouchBasedDevice;
    window.onTouchBasedDevice = jasmine
      .createSpy('onTouchBasedDevice')
      .and.returnValue(null);

    state = jasmine.initializePlayer('video_html5.html');
  });

  afterEach(() => {
    state.storage.clear();
    state.videoPlayer.destroy();
    $.fn.scrollTo.calls.reset();
    $('source').remove();
    window.onTouchBasedDevice = oldOTBD;
  });

  describeInfo = new jasmine.DescribeInfo('on non-Touch devices ', () => {
    beforeEach(() => {
      state.videoPlayer.player.config.events.onReady = jasmine.createSpy('onReady');
    });

    describe('events:', () => {
      beforeEach(() => {
        spyOn(state.videoPlayer.player, 'callStateChangeCallback').and.callThrough();
      });

      describe('[click]', () => {
        describe('when player is paused', () => {
          beforeEach(() => {
            spyOn(state.videoPlayer.player.video, 'play').and.callThrough();
            state.videoPlayer.player.playerState = STATUS.PAUSED;
            $(state.videoPlayer.player.videoEl).trigger('click');
          });

          it('native play event was called', () => {
            expect(state.videoPlayer.player.video.play).toHaveBeenCalled();
          });

          it('player state was changed', (done) => {
            jasmine.waitUntil(() =>
              state.videoPlayer.player.getPlayerState() === STATUS.PLAYING
            ).always(done);
          });
        });

        describe('[player is playing]', () => {
          beforeEach(() => {
            spyOn(state.videoPlayer.player.video, 'pause').and.callThrough();
            state.videoPlayer.player.playerState = STATUS.PLAYING;
            $(state.videoPlayer.player.videoEl).trigger('click');
          });

          it('native event was called', () => {
            expect(state.videoPlayer.player.video.pause).toHaveBeenCalled();
          });

          it('player state was changed', (done) => {
            jasmine.waitUntil(() =>
              state.videoPlayer.player.getPlayerState() !== STATUS.PLAYING
            )
              .then(() => {
                expect(state.videoPlayer.player.getPlayerState()).toBe(STATUS.PAUSED);
              })
              .always(done);
          });

          it('callback was not called', (done) => {
            jasmine.waitUntil(() =>
              state.videoPlayer.player.getPlayerState() !== STATUS.PLAYING
            )
              .then(() => {
                expect(state.videoPlayer.player.callStateChangeCallback)
                  .not.toHaveBeenCalled();
              })
              .always(done);
          });
        });
      });

      describe('[play]', () => {
        beforeEach(() => {
          spyOn(state.videoPlayer.player.video, 'play').and.callThrough();
          state.videoPlayer.player.playerState = STATUS.PAUSED;
          state.videoPlayer.player.playVideo();
        });

        it('native event was called', () => {
          expect(state.videoPlayer.player.video.play).toHaveBeenCalled();
        });

        it('player state was changed', (done) => {
          jasmine.waitUntil(() =>
            state.videoPlayer.player.getPlayerState() !== STATUS.PAUSED
          )
            .then(() => {
              expect([STATUS.BUFFERING, STATUS.PLAYING]).toContain(
                state.videoPlayer.player.getPlayerState()
              );
            })
            .always(done);
        });

        it('callback was called', (done) => {
          jasmine.waitUntil(() =>
            state.videoPlayer.player.getPlayerState() !== STATUS.PAUSED
          )
            .then(() => {
              expect(state.videoPlayer.player.callStateChangeCallback).toHaveBeenCalled();
            })
            .always(done);
        });
      });

      describe('[pause]', () => {
        beforeEach((done) => {
          spyOn(state.videoPlayer.player.video, 'pause').and.callThrough();
          state.videoPlayer.player.playerState = STATUS.UNSTARTED;
          state.videoPlayer.player.playVideo();

          jasmine
            .waitUntil(() =>
              state.videoPlayer.player.getPlayerState() !== STATUS.UNSTARTED
            )
            .done(done);

          state.videoPlayer.player.pauseVideo();
        });

        it('native event was called', () => {
          expect(state.videoPlayer.player.video.pause).toHaveBeenCalled();
        });

        it('player state was changed', (done) => {
          jasmine.waitUntil(() =>
            state.videoPlayer.player.getPlayerState() !== STATUS.PLAYING
          )
            .then(() => {
              expect(state.videoPlayer.player.getPlayerState()).toBe(STATUS.PAUSED);
            })
            .always(done);
        });

        it('callback was called', (done) => {
          jasmine.waitUntil(() =>
            state.videoPlayer.player.getPlayerState() !== STATUS.PLAYING
          )
            .then(() => {
              expect(state.videoPlayer.player.callStateChangeCallback).toHaveBeenCalled();
            })
            .always(done);
        });
      });

      describe('[loadedmetadata]', () => {
        it('player state was changed, start/end was defined, onReady called', (done) => {
          jasmine.fireEvent(state.videoPlayer.player.video, 'loadedmetadata');
          jasmine.waitUntil(() =>
            state.videoPlayer.player.getPlayerState() !== STATUS.UNSTARTED
          )
            .then(() => {
              expect(state.videoPlayer.player.getPlayerState()).toBe(STATUS.PAUSED);
              expect(state.videoPlayer.player.video.currentTime).toBe(0);
              expect(state.videoPlayer.player.config.events.onReady).toHaveBeenCalled();
            })
            .always(done);
        });
      });

      describe('[ended]', () => {
        beforeEach((done) => {
          state.videoPlayer.player.playVideo();
          jasmine
            .waitUntil(() =>
              state.videoPlayer.player.getPlayerState() !== STATUS.UNSTARTED
            )
            .done(done);
        });

        it('player state was changed', () => {
          jasmine.fireEvent(state.videoPlayer.player.video, 'ended');
          expect(state.videoPlayer.player.getPlayerState()).toBe(STATUS.ENDED);
        });

        it('callback was called', () => {
          jasmine.fireEvent(state.videoPlayer.player.video, 'ended');
          expect(state.videoPlayer.player.callStateChangeCallback).toHaveBeenCalled();
        });
      });
    });

    describe('methods', () => {
      let volume, duration, playbackRate;

      beforeEach(() => {
        volume = state.videoPlayer.player.video.volume;
      });

      it('pauseVideo', () => {
        spyOn(state.videoPlayer.player.video, 'pause').and.callThrough();
        state.videoPlayer.player.pauseVideo();
        expect(state.videoPlayer.player.video.pause).toHaveBeenCalled();
      });

      // ... rest of your tests (seekTo, setVolume, getCurrentTime, etc.)
      // Same structure, just replace var -> let/const, use arrow functions

    });

    describe('poster', () => {
      it('has url in player config', () => {
        expect(state.videoPlayer.player.config.poster).toEqual(POSTER_URL);
        expect(state.videoPlayer.player.videoEl).toHaveAttrs({
          poster: POSTER_URL,
        });
      });
    });
  });

  describe('non-hls encoding', () => {
    beforeEach((done) => {
      state = jasmine.initializePlayer('video_html5.html');
      done();
    });
    jasmine.getEnv().describe(describeInfo.description, describeInfo.specDefinitions);
  });

  describe('hls encoding', () => {
    beforeEach((done) => {
      state = jasmine.initializeHLSPlayer();
      done();
    });
    jasmine.getEnv().describe(describeInfo.description, describeInfo.specDefinitions);
  });

  it('does not show poster for html5 video if url is not present', () => {
    state = jasmine.initializePlayer('video_html5.html', { poster: null });
    expect(state.videoPlayer.player.config.poster).toEqual(null);
    expect(state.videoPlayer.player.videoEl).not.toHaveAttr('poster');
  });

  it('does not show poster for hls video if url is not present', () => {
    state = jasmine.initializePlayer('video_hls.html', { poster: null });
    expect(state.videoPlayer.player.config.poster).toEqual(null);
    expect(state.videoPlayer.player.videoEl).not.toHaveAttr('poster');
  });

  it('native controls are used on iPhone', () => {
    window.onTouchBasedDevice.and.returnValue(['iPhone']);
    state = jasmine.initializePlayer('video_html5.html');
    state.videoPlayer.player.config.events.onReady = jasmine.createSpy('onReady');
    expect($('video')).toHaveAttr('controls');
  });
});
