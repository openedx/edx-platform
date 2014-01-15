(function() {
  describe('VideoControl', function() {
    var state, oldOTBD;

    function initialize(fixture) {
      if (fixture) {
        loadFixtures(fixture);
      } else {
        loadFixtures('video_all.html');
      }

      debugger;

      state = new Video('#example');
    }

    function initializeYouTube() {
        initialize('video.html');
    }

    beforeEach(function(){
        oldOTBD = window.onTouchBasedDevice;
        window.onTouchBasedDevice = jasmine.createSpy('onTouchBasedDevice').andReturn(null);
    });

    afterEach(function() {
        $('source').remove();
        window.onTouchBasedDevice = oldOTBD;
    });

    describe('constructor', function() {
      beforeEach(function() {
        initialize();
      });

      it('render the video controls', function() {
        expect($('.video-controls')).toContain(
          ['.slider', 'ul.vcr', 'a.play', '.vidtime', '.add-fullscreen'].join(',')
        );
        expect($('.video-controls').find('.vidtime')).toHaveText('0:00 / 0:00');
      });

      it('add ARIA attributes to time control', function () {


        var timeControl = $('div.slider>a');
        expect(timeControl).toHaveAttrs({
          'role': 'slider',
          'title': 'video position',
          'aria-disabled': 'false'
        });
        expect(timeControl).toHaveAttr('aria-valuetext');
      });

      it('add ARIA attributes to play control', function () {
        var playControl = $('ul.vcr a');
        expect(playControl).toHaveAttrs({
          'role': 'button',
          'title': 'Play',
          'aria-disabled': 'false'
        });
      });

      it('add ARIA attributes to fullscreen control', function () {
        var fullScreenControl = $('a.add-fullscreen');
        expect(fullScreenControl).toHaveAttrs({
          'role': 'button',
          'title': 'Fill browser',
          'aria-disabled': 'false'
        });
      });

      it('bind the playback button', function() {
        waitsFor(function () {
          return typeof state.videoControl !== 'undefined';
        }, 'videoControl is defined', 1000);

        runs(function () {
          expect($('.video_control')).toHandleWith('click', state.videoControl.togglePlayback);
        });
      });

      describe('when on a non-touch based device', function() {
        beforeEach(function() {
          initialize();
        });

        it('add the play class to video control', function() {
          expect($('.video_control')).toHaveClass('play');
          expect($('.video_control')).toHaveAttr('title', 'Play');
        });
      });

      describe('when on a touch based device', function() {
        beforeEach(function() {
          window.onTouchBasedDevice.andReturn(['iPad']);
          initialize();
        });

        it('does not add the play class to video control', function() {
          expect($('.video_control')).toHaveClass('play');
          expect($('.video_control')).toHaveAttr('title', 'Play');
        });
      });
    });

    describe('play', function() {
      beforeEach(function() {
        initialize();
      });

      it('switch playback button to play state', function() {
        waitsFor(function () {
          return typeof state.videoControl !== 'undefined';
        }, 'videoControl is defined', 1000);

        runs(function () {
          state.videoControl.play();

          expect($('.video_control')).not.toHaveClass('play');
          expect($('.video_control')).toHaveClass('pause');
          expect($('.video_control')).toHaveAttr('title', 'Pause');
        });
      });
    });

    describe('pause', function() {
      beforeEach(function() {
        initialize();
      });

      it('switch playback button to pause state', function() {
        waitsFor(function () {
          return typeof state.videoControl !== 'undefined';
        }, 'videoControl is defined', 1000);

        runs(function () {
          state.videoControl.pause();

          expect($('.video_control')).not.toHaveClass('pause');
          expect($('.video_control')).toHaveClass('play');
          expect($('.video_control')).toHaveAttr('title', 'Play');
        });
      });
    });

    describe('togglePlayback', function() {
      beforeEach(function() {
        initialize();
      });

      describe('when the control does not have play or pause class', function() {
        beforeEach(function() {
          $('.video_control').removeClass('play').removeClass('pause');
        });

        describe('when the video is playing', function() {
          beforeEach(function() {
            $('.video_control').addClass('play');
            spyOnEvent(videoControl, 'pause');
            videoControl.togglePlayback(jQuery.Event('click'));
          });

          it('does not trigger the pause event', function() {
            expect('pause').not.toHaveBeenTriggeredOn(videoControl);
          });
        });

        describe('when the video is paused', function() {
          beforeEach(function() {
            $('.video_control').addClass('pause');
            spyOnEvent(videoControl, 'play');
            videoControl.togglePlayback(jQuery.Event('click'));
          });

          it('does not trigger the play event', function() {
            expect('play').not.toHaveBeenTriggeredOn(videoControl);
          });
        });
      });
    });

    describe('Play placeholder', function () {
      var oldYT,
        cases = [{
            name: 'PC',
            isShown: false,
            isTouch: null
          }, {
            name: 'iPad',
            isShown: true,
            isTouch: ['iPad']
          }, {
            name: 'Android',
            isShown: true,
            isTouch: ['Android']
          }, {
            name: 'iPhone',
            isShown: false,
            isTouch: ['iPhone']
        }];

      beforeEach(function () {
        oldYT = window.YT;

        jasmine.stubRequests();
        window.YT = {
          Player: function () {
            return {
              getDuration: function () {
                return 60;
              }
            };
          },
          PlayerState: oldYT.PlayerState,
          ready: function (callback) {
              callback();
          }
        };

        spyOn(window.YT, 'Player').andCallThrough();
      });

      afterEach(function () {
        window.YT = oldYT;
      });

      it('works correctly on calling proper methods', function () {
        initialize();

        waitsFor(function () {
          return typeof state.videoControl !== 'undefined';
        }, 'videoControl is defined', 1000);

        runs(function () {
          var btnPlay = state.el.find('.btn-play');

          state.videoControl.showPlayPlaceholder();

          expect(btnPlay).not.toHaveClass('is-hidden');
          expect(btnPlay).toHaveAttrs({
            'aria-hidden': 'false',
            'tabindex': 0
          });

          state.videoControl.hidePlayPlaceholder();

          expect(btnPlay).toHaveClass('is-hidden');
          expect(btnPlay).toHaveAttrs({
            'aria-hidden': 'true',
            'tabindex': -1
          });
        });
      });

      $.each(cases, function(index, data) {
        var message = [
            (data.isShown) ? 'is' : 'is not',
            ' shown on',
            data.name
          ].join('');

        it(message, function () {
          window.onTouchBasedDevice.andReturn(data.isTouch);
          initialize();
          var btnPlay = state.el.find('.btn-play');

          if (data.isShown) {
            expect(btnPlay).not.toHaveClass('is-hidden');
          } else {
            expect(btnPlay).toHaveClass('is-hidden');
          }
        });
      });

      $.each(['iPad', 'Android'], function(index, device) {
        it('is shown on paused video on '+ device +' in HTML5 player', function () {
          window.onTouchBasedDevice.andReturn([device]);
          initialize();

          waitsFor(function () {
            return typeof state.videoControl !== 'undefined';
          }, 'videoControl is defined', 1000);

          runs(function () {
            var btnPlay = state.el.find('.btn-play');

            state.videoControl.play();
            state.videoControl.pause();

            expect(btnPlay).not.toHaveClass('is-hidden');
          });
        });

        it('is hidden on playing video on '+ device +' in HTML5 player', function () {
          window.onTouchBasedDevice.andReturn([device]);
          initialize();

          waitsFor(function () {
            return typeof state.videoControl !== 'undefined';
          }, 'videoControl is defined', 1000);

          runs(function () {
            var btnPlay = state.el.find('.btn-play');

            state.videoControl.play();

            expect(btnPlay).toHaveClass('is-hidden');
          });
        });

        it('is hidden on paused video on '+ device +' in YouTube player', function () {
          var btnPlay;

          window.onTouchBasedDevice.andReturn([device]);
          initializeYouTube();

          waitsFor(function () {
            return typeof state.videoControl !== 'undefined';
          }, 'videoControl is defined', 1000);

          runs(function () {
            btnPlay = state.el.find('.btn-play');

            state.videoControl.play();
            state.videoControl.pause();

            expect(btnPlay).toHaveClass('is-hidden');
          });
        });
      });
    });

    it('show', function () {
      initialize();

      waitsFor(function () {
        return typeof state.videoControl !== 'undefined';
      }, 'videoControl is defined', 1000);

      runs(function () {
        var controls = state.el.find('.video-controls');
        controls.addClass('is-hidden');

        state.videoControl.show();
        expect(controls).not.toHaveClass('is-hidden');
      });
    });
  });

}).call(this);
