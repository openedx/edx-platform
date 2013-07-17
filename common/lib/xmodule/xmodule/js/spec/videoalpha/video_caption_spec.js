(function() {
  xdescribe('VideoCaptionAlpha', function() {
    var state, videoPlayer, videoCaption, videoSpeedControl;

    function initialize() {
      loadFixtures('videoalpha_all.html');
      state = new VideoAlpha('#example');
      videoPlayer = state.videoPlayer;
      videoCaption = state.videoCaption;
      videoSpeedControl = state.videoSpeedControl;
    }

    beforeEach(function() {
      initialize();
      window.onTouchBasedDevice = jasmine.createSpy('onTouchBasedDevice').andReturn(false);
    });

    afterEach(function() {
      YT.Player = void 0;
      $.fn.scrollTo.reset();
      $('.subtitles').remove();
    });

    describe('constructor', function() {
      describe('always', function() {
        beforeEach(function() {
          spyOn($, 'getWithPrefix').andCallThrough();
          initialize();
        });

        it('create the caption element', function() {
          expect($('.videoalpha')).toContain('ol.subtitles');
        });

        it('add caption control to video player', function() {
          expect($('.videoalpha')).toContain('a.hide-subtitles');
        });

        it('fetch the caption', function() {
          waitsFor(function () {
            if (videoCaption.loaded === true) {
                return true;
            }

            return false;
          }, 'Expect captions to be loaded.', 1000);

          runs(function () {
              expect($.getWithPrefix).toHaveBeenCalledWith(videoCaption.captionURL(), jasmine.any(Function));
          });
        });

        it('bind window resize event', function() {
          expect($(window)).toHandleWith('resize', videoCaption.resize);
        });

        it('bind the hide caption button', function() {
          expect($('.hide-subtitles')).toHandleWith('click', videoCaption.toggle);
        });

        it('bind the mouse movement', function() {
          expect($('.subtitles')).toHandleWith('mouseover', videoCaption.onMouseEnter);
          expect($('.subtitles')).toHandleWith('mouseout', videoCaption.onMouseLeave);
          expect($('.subtitles')).toHandleWith('mousemove', videoCaption.onMovement);
          expect($('.subtitles')).toHandleWith('mousewheel', videoCaption.onMovement);
          expect($('.subtitles')).toHandleWith('DOMMouseScroll', videoCaption.onMovement);
        });
      });

      describe('when on a non touch-based device', function() {
        beforeEach(function() {
          initialize();
        });

        it('render the caption', function() {
          var captionsData;

          captionsData = jasmine.stubbedCaption;
          $('.subtitles li[data-index]').each(function(index, link) {
            expect($(link)).toHaveData('index', index);
            expect($(link)).toHaveData('start', captionsData.start[index]);
            expect($(link)).toHaveText(captionsData.text[index]);
          });
        });

        it('add a padding element to caption', function() {
          expect($('.subtitles li:first').hasClass('spacing')).toBe(true);
          expect($('.subtitles li:last').hasClass('spacing')).toBe(true);
        });

        it('bind all the caption link', function() {
          $('.subtitles li[data-index]').each(function(index, link) {
            expect($(link)).toHandleWith('click', videoCaption.seekPlayer);
          });
        });

        it('set rendered to true', function() {
          expect(videoCaption.rendered).toBeTruthy();
        });
      });

      describe('when on a touch-based device', function() {
        beforeEach(function() {
          window.onTouchBasedDevice.andReturn(true);
          initialize();
        });

        it('show explaination message', function() {
          expect($('.subtitles li')).toHaveHtml("Caption will be displayed when you start playing the video.");
        });

        it('does not set rendered to true', function() {
          expect(videoCaption.rendered).toBeFalsy();
        });
      });
    });

    describe('mouse movement', function() {
      beforeEach(function() {
        initialize();
        window.setTimeout.andReturn(100);
        spyOn(window, 'clearTimeout');
      });

      describe('when cursor is outside of the caption box', function() {
        beforeEach(function() {
          $(window).trigger(jQuery.Event('mousemove'));
        });

        it('does not set freezing timeout', function() {
          expect(videoCaption.frozen).toBeFalsy();
        });
      });

      describe('when cursor is in the caption box', function() {
        beforeEach(function() {
          $('.subtitles').trigger(jQuery.Event('mouseenter'));
        });

        it('set the freezing timeout', function() {
          expect(videoCaption.frozen).toEqual(100);
        });

        describe('when the cursor is moving', function() {
          beforeEach(function() {
            $('.subtitles').trigger(jQuery.Event('mousemove'));
          });

          it('reset the freezing timeout', function() {
            expect(window.clearTimeout).toHaveBeenCalledWith(100);
          });
        });

        describe('when the mouse is scrolling', function() {
          beforeEach(function() {
            $('.subtitles').trigger(jQuery.Event('mousewheel'));
          });

          it('reset the freezing timeout', function() {
            expect(window.clearTimeout).toHaveBeenCalledWith(100);
          });
        });
      });

      describe('when cursor is moving out of the caption box', function() {
        beforeEach(function() {
          videoCaption.frozen = 100;
          $.fn.scrollTo.reset();
        });

        describe('always', function() {
          beforeEach(function() {
            $('.subtitles').trigger(jQuery.Event('mouseout'));
          });

          it('reset the freezing timeout', function() {
            expect(window.clearTimeout).toHaveBeenCalledWith(100);
          });

          it('unfreeze the caption', function() {
            expect(videoCaption.frozen).toBeNull();
          });
        });

        describe('when the player is playing', function() {
          beforeEach(function() {
            videoCaption.playing = true;
            $('.subtitles li[data-index]:first').addClass('current');
            $('.subtitles').trigger(jQuery.Event('mouseout'));
          });

          it('scroll the caption', function() {
            expect($.fn.scrollTo).toHaveBeenCalled();
          });
        });

        describe('when the player is not playing', function() {
          beforeEach(function() {
            videoCaption.playing = false;
            $('.subtitles').trigger(jQuery.Event('mouseout'));
          });

          it('does not scroll the caption', function() {
            expect($.fn.scrollTo).not.toHaveBeenCalled();
          });
        });
      });
    });

    describe('search', function() {
      beforeEach(function() {
        initialize();
      });

      it('return a correct caption index', function() {
        expect(videoCaption.search(0)).toEqual(0);
        expect(videoCaption.search(3120)).toEqual(1);
        expect(videoCaption.search(6270)).toEqual(2);
        expect(videoCaption.search(8490)).toEqual(2);
        expect(videoCaption.search(21620)).toEqual(4);
        expect(videoCaption.search(24920)).toEqual(5);
      });
    });

    describe('play', function() {
      describe('when the caption was not rendered', function() {
        beforeEach(function() {
          window.onTouchBasedDevice.andReturn(true);
          initialize();
          videoCaption.play();
        });

        it('render the caption', function() {
          var captionsData;

          captionsData = jasmine.stubbedCaption;
          $('.subtitles li[data-index]').each(function(index, link) {
            expect($(link)).toHaveData('index', index);
            expect($(link)).toHaveData('start', captionsData.start[index]);
            expect($(link)).toHaveText(captionsData.text[index]);
          });
        });

        it('add a padding element to caption', function() {
          expect($('.subtitles li:first')).toBe('.spacing');
          expect($('.subtitles li:last')).toBe('.spacing');
        });

        it('bind all the caption link', function() {
          $('.subtitles li[data-index]').each(function(index, link) {
            expect($(link)).toHandleWith('click', videoCaption.seekPlayer);
          });
        });

        it('set rendered to true', function() {
          expect(videoCaption.rendered).toBeTruthy();
        });

        it('set playing to true', function() {
          expect(videoCaption.playing).toBeTruthy();
        });
      });
    });

    describe('pause', function() {
      beforeEach(function() {
        initialize();
        videoCaption.playing = true;
        videoCaption.pause();
      });

      it('set playing to false', function() {
        expect(videoCaption.playing).toBeFalsy();
      });
    });

    describe('updatePlayTime', function() {
      beforeEach(function() {
        initialize();
      });

      describe('when the video speed is 1.0x', function() {
        beforeEach(function() {
          videoSpeedControl.currentSpeed = '1.0';
          videoCaption.updatePlayTime(25.000);
        });

        it('search the caption based on time', function() {
          expect(videoCaption.currentIndex).toEqual(5);
        });
      });

      describe('when the video speed is not 1.0x', function() {
        beforeEach(function() {
          videoSpeedControl.currentSpeed = '0.75';
          videoCaption.updatePlayTime(25.000);
        });

        it('search the caption based on 1.0x speed', function() {
          expect(videoCaption.currentIndex).toEqual(5);
        });
      });

      describe('when the index is not the same', function() {
        beforeEach(function() {
          videoCaption.currentIndex = 1;
          $('.subtitles li[data-index=5]').addClass('current');
          videoCaption.updatePlayTime(25.000);
        });

        it('deactivate the previous caption', function() {
          expect($('.subtitles li[data-index=1]')).not.toHaveClass('current');
        });

        it('activate new caption', function() {
          expect($('.subtitles li[data-index=5]')).toHaveClass('current');
        });

        it('save new index', function() {
          expect(videoCaption.currentIndex).toEqual(5);
        });

        it('scroll caption to new position', function() {
          expect($.fn.scrollTo).toHaveBeenCalled();
        });
      });

      describe('when the index is the same', function() {
        beforeEach(function() {
          videoCaption.currentIndex = 1;
          $('.subtitles li[data-index=3]').addClass('current');
          videoCaption.updatePlayTime(15.000);
        });

        it('does not change current subtitle', function() {
          expect($('.subtitles li[data-index=3]')).toHaveClass('current');
        });
      });
    });

    describe('resize', function() {
      beforeEach(function() {
        initialize();
        $('.subtitles li[data-index=1]').addClass('current');
        videoCaption.resize();
      });

      it('set the height of caption container', function() {
        expect(parseInt($('.subtitles').css('maxHeight'), 10)).toBeCloseTo($('.video-wrapper').height(), 2);
      });

      it('set the height of caption spacing', function() {
        var firstSpacing, lastSpacing;
        firstSpacing = Math.abs(parseInt($('.subtitles .spacing:first').css('height'), 10));
        lastSpacing = Math.abs(parseInt($('.subtitles .spacing:last').css('height'), 10));
        expect(firstSpacing - videoCaption.topSpacingHeight()).toBeLessThan(1);
        expect(lastSpacing - videoCaption.bottomSpacingHeight()).toBeLessThan(1);
      });

      it('scroll caption to new position', function() {
        expect($.fn.scrollTo).toHaveBeenCalled();
      });
    });

    describe('scrollCaption', function() {
      beforeEach(function() {
        initialize();
      });

      describe('when frozen', function() {
        beforeEach(function() {
          videoCaption.frozen = true;
          $('.subtitles li[data-index=1]').addClass('current');
          videoCaption.scrollCaption();
        });

        it('does not scroll the caption', function() {
          expect($.fn.scrollTo).not.toHaveBeenCalled();
        });
      });

      describe('when not frozen', function() {
        beforeEach(function() {
          videoCaption.frozen = false;
        });

        describe('when there is no current caption', function() {
          beforeEach(function() {
            videoCaption.scrollCaption();
          });

          it('does not scroll the caption', function() {
            expect($.fn.scrollTo).not.toHaveBeenCalled();
          });
        });

        describe('when there is a current caption', function() {
          beforeEach(function() {
            $('.subtitles li[data-index=1]').addClass('current');
            videoCaption.scrollCaption();
          });

          it('scroll to current caption', function() {
            // Check for calledWith(parameters) for some reason fails...
            //
            // var offset = -0.5 * ($('.video-wrapper').height() - $('.subtitles .current:first').height());
            //
            // expect($.fn.scrollTo).toHaveBeenCalledWith(
            //   $('.subtitles .current:first', videoCaption.el),
            //   {
            //     offset: offset
            //   }
            // );

            expect($.fn.scrollTo).toHaveBeenCalled();
          });
        });
      });
    });

    describe('seekPlayer', function() {
      describe('when the video speed is 1.0x', function() {
        beforeEach(function() {
          initialize();
          videoSpeedControl.currentSpeed = '1.0';
          $('.subtitles li[data-start="14910"]').trigger('click');
        });

        it('trigger seek event with the correct time', function() {
          expect(videoPlayer.currentTime).toEqual(15);
        });
      });

      describe('when the video speed is not 1.0x', function() {
        beforeEach(function() {
          initialize();
          videoSpeedControl.currentSpeed = '0.75';
          $('.subtitles li[data-start="14910"]').trigger('click');
        });

        it('trigger seek event with the correct time', function() {
          expect(videoPlayer.currentTime).toEqual(15);
        });
      });
    });

    describe('toggle', function() {
      beforeEach(function() {
        initialize();
        spyOn(videoPlayer, 'log');
        $('.subtitles li[data-index=1]').addClass('current');
      });

      describe('when the caption is visible', function() {
        beforeEach(function() {
          state.el.removeClass('closed');
          videoCaption.toggle(jQuery.Event('click'));
        });

        it('log the hide_transcript event', function() {
          expect(videoPlayer.log).toHaveBeenCalledWith('hide_transcript', {
            currentTime: videoPlayer.currentTime
          });
        });

        it('hide the caption', function() {
          expect(state.el).toHaveClass('closed');
        });
      });

      describe('when the caption is hidden', function() {
        beforeEach(function() {
          state.el.addClass('closed');
          videoCaption.toggle(jQuery.Event('click'));
        });

        it('log the show_transcript event', function() {
          expect(videoPlayer.log).toHaveBeenCalledWith('show_transcript', {
            currentTime: videoPlayer.currentTime
          });
        });

        it('show the caption', function() {
          expect(state.el).not.toHaveClass('closed');
        });

        it('scroll the caption', function() {
          expect($.fn.scrollTo).toHaveBeenCalled();
        });
      });
    });
  });

}).call(this);
