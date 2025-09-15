/* eslint-disable no-undef */

describe('Video HTML5Video', () => {
  const STATUS = window.STATUS
  let state
  let oldOTBD
  const playbackRates = [0.75, 1.0, 1.25, 1.5, 2.0]
  let describeInfo
  const POSTER_URL = '/media/video-images/poster.png'

  beforeEach(() => {
    oldOTBD = window.onTouchBasedDevice
    window.onTouchBasedDevice = jasmine.createSpy('onTouchBasedDevice').and.returnValue(null)

    state = jasmine.initializePlayer('video_html5.html')
  })

  afterEach(() => {
    state.storage.clear()
    state.videoPlayer.destroy()
    $.fn.scrollTo.calls.reset()
    $('source').remove()
    window.onTouchBasedDevice = oldOTBD
  })

  describeInfo = new jasmine.DescribeInfo('on non-Touch devices ', () => {
    beforeEach(() => {
      state.videoPlayer.player.config.events.onReady = jasmine.createSpy('onReady')
    })

    describe('events:', () => {
      beforeEach(() => {
        spyOn(state.videoPlayer.player, 'callStateChangeCallback').and.callThrough()
      })

      describe('[click]', () => {
        describe('when player is paused', () => {
          beforeEach(() => {
            spyOn(state.videoPlayer.player.video, 'play').and.callThrough()
            state.videoPlayer.player.playerState = STATUS.PAUSED
            $(state.videoPlayer.player.videoEl).trigger('click')
          })

          it('native play event was called', () => {
            expect(state.videoPlayer.player.video.play).toHaveBeenCalled()
          })

          it('player state was changed', done => {
            jasmine.waitUntil(() => state.videoPlayer.player.getPlayerState() === STATUS.PLAYING).always(done)
          })
        })

        describe('[player is playing]', () => {
          beforeEach(() => {
            spyOn(state.videoPlayer.player.video, 'pause').and.callThrough()
            state.videoPlayer.player.playerState = STATUS.PLAYING
            $(state.videoPlayer.player.videoEl).trigger('click')
          })

          it('native event was called', () => {
            expect(state.videoPlayer.player.video.pause).toHaveBeenCalled()
          })

          it('player state was changed', done => {
            jasmine
              .waitUntil(() => state.videoPlayer.player.getPlayerState() !== STATUS.PLAYING)
              .then(() => {
                expect(state.videoPlayer.player.getPlayerState()).toBe(STATUS.PAUSED)
              })
              .always(done)
          })

          it('callback was not called', done => {
            jasmine
              .waitUntil(() => state.videoPlayer.player.getPlayerState() !== STATUS.PLAYING)
              .then(() => {
                expect(state.videoPlayer.player.callStateChangeCallback).not.toHaveBeenCalled()
              })
              .always(done)
          })
        })
      })

      describe('[play]', () => {
        beforeEach(() => {
          spyOn(state.videoPlayer.player.video, 'play').and.callThrough()
          state.videoPlayer.player.playerState = STATUS.PAUSED
          state.videoPlayer.player.playVideo()
        })

        it('native event was called', () => {
          expect(state.videoPlayer.player.video.play).toHaveBeenCalled()
        })

        it('player state was changed', done => {
          jasmine
            .waitUntil(() => state.videoPlayer.player.getPlayerState() !== STATUS.PAUSED)
            .then(() => {
              expect([STATUS.BUFFERING, STATUS.PLAYING]).toContain(state.videoPlayer.player.getPlayerState())
            })
            .always(done)
        })

        it('callback was called', done => {
          jasmine
            .waitUntil(() => state.videoPlayer.player.getPlayerState() !== STATUS.PAUSED)
            .then(() => {
              expect(state.videoPlayer.player.callStateChangeCallback).toHaveBeenCalled()
            })
            .always(done)
        })
      })

      describe('[pause]', () => {
        beforeEach(done => {
          spyOn(state.videoPlayer.player.video, 'pause').and.callThrough()
          state.videoPlayer.player.playerState = STATUS.UNSTARTED
          state.videoPlayer.player.playVideo()

          jasmine.waitUntil(() => state.videoPlayer.player.getPlayerState() !== STATUS.UNSTARTED).done(done)

          state.videoPlayer.player.pauseVideo()
        })

        it('native event was called', () => {
          expect(state.videoPlayer.player.video.pause).toHaveBeenCalled()
        })

        it('player state was changed', done => {
          jasmine
            .waitUntil(() => state.videoPlayer.player.getPlayerState() !== STATUS.PLAYING)
            .then(() => {
              expect(state.videoPlayer.player.getPlayerState()).toBe(STATUS.PAUSED)
            })
            .always(done)
        })

        it('callback was called', done => {
          jasmine
            .waitUntil(() => state.videoPlayer.player.getPlayerState() !== STATUS.PLAYING)
            .then(() => {
              expect(state.videoPlayer.player.callStateChangeCallback).toHaveBeenCalled()
            })
            .always(done)
        })
      })

      describe('[loadedmetadata]', () => {
        it('player state was changed, start/end was defined, onReady called', done => {
          jasmine.fireEvent(state.videoPlayer.player.video, 'loadedmetadata')
          jasmine
            .waitUntil(() => state.videoPlayer.player.getPlayerState() !== STATUS.UNSTARTED)
            .then(() => {
              expect(state.videoPlayer.player.getPlayerState()).toBe(STATUS.PAUSED)
              expect(state.videoPlayer.player.video.currentTime).toBe(0)
              expect(state.videoPlayer.player.config.events.onReady).toHaveBeenCalled()
            })
            .always(done)
        })
      })

      describe('[ended]', () => {
        beforeEach(done => {
          state.videoPlayer.player.playVideo()
          jasmine.waitUntil(() => state.videoPlayer.player.getPlayerState() !== STATUS.UNSTARTED).done(done)
        })

        it('player state was changed', () => {
          jasmine.fireEvent(state.videoPlayer.player.video, 'ended')
          expect(state.videoPlayer.player.getPlayerState()).toBe(STATUS.ENDED)
        })

        it('callback was called', () => {
          jasmine.fireEvent(state.videoPlayer.player.video, 'ended')
          expect(state.videoPlayer.player.callStateChangeCallback).toHaveBeenCalled()
        })
      })
    })

    describe('methods', () => {
      let volume, duration, playbackRate

      beforeEach(() => {
        volume = state.videoPlayer.player.video.volume
      })

      it('pauseVideo', () => {
        spyOn(state.videoPlayer.player.video, 'pause').and.callThrough()
        state.videoPlayer.player.pauseVideo()
        expect(state.videoPlayer.player.video.pause).toHaveBeenCalled()
      })

      describe('seekTo', () => {
        it('set new correct value', done => {
          state.videoPlayer.player.playVideo()
          jasmine
            .waitUntil(function () {
              return state.videoPlayer.player.getPlayerState() === STATUS.PLAYING
            })
            .then(function () {
              state.videoPlayer.player.seekTo(2)
              expect(state.videoPlayer.player.getCurrentTime()).toBe(2)
            })
            .done(done)
        })

        it('set new incorrect values', () => {
          // eslint-disable-next-line no-shadow
          var seek = state.videoPlayer.player.video.currentTime
          state.videoPlayer.player.seekTo(-50)
          expect(state.videoPlayer.player.getCurrentTime()).toBe(seek)
          state.videoPlayer.player.seekTo('5')
          expect(state.videoPlayer.player.getCurrentTime()).toBe(seek)
          state.videoPlayer.player.seekTo(500000)
          expect(state.videoPlayer.player.getCurrentTime()).toBe(seek)
        })
      })

      describe('setVolume', () => {
        it('set new correct value', () => {
          state.videoPlayer.player.setVolume(50)
          expect(state.videoPlayer.player.getVolume()).toBe(50 * 0.01)
        })

        it('set new incorrect values', () => {
          state.videoPlayer.player.setVolume(-50)
          expect(state.videoPlayer.player.getVolume()).toBe(volume)
          state.videoPlayer.player.setVolume('5')
          expect(state.videoPlayer.player.getVolume()).toBe(volume)
          state.videoPlayer.player.setVolume(500000)
          expect(state.videoPlayer.player.getVolume()).toBe(volume)
        })
      })

      it('getCurrentTime', done => {
        state.videoPlayer.player.playVideo()
        jasmine
          .waitUntil(() => {
            return state.videoPlayer.player.getPlayerState() === STATUS.PLAYING
          })
          .then(() => {
            state.videoPlayer.player.video.currentTime = 3
            expect(state.videoPlayer.player.getCurrentTime()).toBe(state.videoPlayer.player.video.currentTime)
          })
          .done(done)
      })

      it('playVideo', () => {
        spyOn(state.videoPlayer.player.video, 'play').and.callThrough()
        state.videoPlayer.player.playVideo()
        expect(state.videoPlayer.player.video.play).toHaveBeenCalled()
      })

      it('getPlayerState', () => {
        state.videoPlayer.player.playerState = STATUS.PLAYING
        expect(state.videoPlayer.player.getPlayerState()).toBe(STATUS.PLAYING)
        state.videoPlayer.player.playerState = STATUS.ENDED
        expect(state.videoPlayer.player.getPlayerState()).toBe(STATUS.ENDED)
      })

      it('getVolume', () => {
        // eslint-disable-next-line no-multi-assign
        volume = state.videoPlayer.player.video.volume = 0.5
        expect(state.videoPlayer.player.getVolume()).toBe(volume)
      })

      it('getDuration', done => {
        state.videoPlayer.player.playVideo()
        jasmine
          .waitUntil(() => {
            return state.videoPlayer.player.getPlayerState() === STATUS.PLAYING
          })
          .then(() => {
            duration = state.videoPlayer.player.video.duration
            expect(state.videoPlayer.player.getDuration()).toBe(duration)
          })
          .always(done)
      })

      describe('setPlaybackRate', () => {
        it('set a slow value', () => {
          playbackRate = 0.75
          state.videoPlayer.player.setPlaybackRate(playbackRate)
          expect(state.videoPlayer.player.video.playbackRate).toBe(playbackRate)
        })

        it('set a fast value', () => {
          playbackRate = 2.0
          state.videoPlayer.player.setPlaybackRate(playbackRate)
          expect(state.videoPlayer.player.video.playbackRate).toBe(playbackRate)
        })

        it('set NaN value', () => {
          var oldPlaybackRate = state.videoPlayer.player.video.playbackRate

          // When we try setting the playback rate to some
          // non-numerical value, nothing should happen.
          playbackRate = NaN
          state.videoPlayer.player.setPlaybackRate(playbackRate)
          expect(state.videoPlayer.player.video.playbackRate).toBe(oldPlaybackRate)
        })
      })

      it('getAvailablePlaybackRates', () => {
        expect(state.videoPlayer.player.getAvailablePlaybackRates()).toEqual(playbackRates)
      })

      it('_getLogs', done => {
        state.videoPlayer.player.playVideo()
        jasmine
          .waitUntil(() => {
            return state.videoPlayer.player.getPlayerState() === STATUS.PLAYING
          })
          .then(() => {
            var logs = state.videoPlayer.player._getLogs()
            expect(logs).toEqual(jasmine.any(Array))
            expect(logs.length).toBeGreaterThan(0)
          })
          .done(done)
      })
    })

    describe('poster', () => {
      it('has url in player config', () => {
        expect(state.videoPlayer.player.config.poster).toEqual(POSTER_URL)
        expect(state.videoPlayer.player.videoEl).toHaveAttrs({
          poster: POSTER_URL
        })
      })
    })
  })

  describe('non-hls encoding', () => {
    beforeEach(done => {
      state = jasmine.initializePlayer('video_html5.html')
      done()
    })
    jasmine.getEnv().describe(describeInfo.description, describeInfo.specDefinitions)
  })

  describe('hls encoding', () => {
    beforeEach(done => {
      state = jasmine.initializeHLSPlayer()
      done()
    })
    jasmine.getEnv().describe(describeInfo.description, describeInfo.specDefinitions)
  })

  it('does not show poster for html5 video if url is not present', () => {
    state = jasmine.initializePlayer('video_html5.html', { poster: null })
    expect(state.videoPlayer.player.config.poster).toEqual(null)
    expect(state.videoPlayer.player.videoEl).not.toHaveAttr('poster')
  })

  it('does not show poster for hls video if url is not present', () => {
    state = jasmine.initializePlayer('video_hls.html', { poster: null })
    expect(state.videoPlayer.player.config.poster).toEqual(null)
    expect(state.videoPlayer.player.videoEl).not.toHaveAttr('poster')
  })

  it('native controls are used on iPhone', () => {
    window.onTouchBasedDevice.and.returnValue(['iPhone'])
    state = jasmine.initializePlayer('video_html5.html')
    state.videoPlayer.player.config.events.onReady = jasmine.createSpy('onReady')
    expect($('video')).toHaveAttr('controls')
  })
})
