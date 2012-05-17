(function() {

  describe('VideoCaption', function() {
    beforeEach(function() {
      return this.player = jasmine.stubVideoPlayer(this);
    });
    afterEach(function() {
      YT.Player = void 0;
      return $.fn.scrollTo.reset();
    });
    describe('constructor', function() {
      beforeEach(function() {
        spyOn($, 'getWithPrefix').andCallThrough();
        return this.caption = new VideoCaption(this.player, 'def456');
      });
      it('set the player', function() {
        return expect(this.caption.player).toEqual(this.player);
      });
      it('set the youtube id', function() {
        return expect(this.caption.youtubeId).toEqual('def456');
      });
      it('create the caption element', function() {
        return expect($('.video')).toContain('ol.subtitles');
      });
      it('add caption control to video player', function() {
        return expect($('.video')).toContain('a.hide-subtitles');
      });
      it('fetch the caption', function() {
        return expect($.getWithPrefix).toHaveBeenCalledWith(this.caption.captionURL(), jasmine.any(Function));
      });
      it('render the caption', function() {
        return expect($('.subtitles').html()).toMatch(new RegExp('<li data-index="0" data-start="0">Caption at 0</li>\n<li data-index="1" data-start="10000">Caption at 10000</li>\n<li data-index="2" data-start="20000">Caption at 20000</li>\n<li data-index="3" data-start="30000">Caption at 30000</li>\n<li data-index="4" data-start="40000">Caption at 40000</li>\n<li data-index="5" data-start="50000">Caption at 50000</li>\n<li data-index="6" data-start="60000">Caption at 60000</li>\n<li data-index="7" data-start="70000">Caption at 70000</li>\n<li data-index="8" data-start="80000">Caption at 80000</li>\n<li data-index="9" data-start="90000">Caption at 90000</li>\n<li data-index="10" data-start="100000">Caption at 100000</li>\n<li data-index="11" data-start="110000">Caption at 110000</li>\n<li data-index="12" data-start="120000">Caption at 120000</li>'.replace(/\n/g, '')));
      });
      it('add a padding element to caption', function() {
        expect($('.subtitles li:first')).toBe('.spacing');
        return expect($('.subtitles li:last')).toBe('.spacing');
      });
      it('bind all the caption link', function() {
        var _this = this;
        return $('.subtitles li[data-index]').each(function(index, link) {
          return expect($(link)).toHandleWith('click', _this.caption.seekPlayer);
        });
      });
      it('bind window resize event', function() {
        return expect($(window)).toHandleWith('resize', this.caption.onWindowResize);
      });
      it('bind player resize event', function() {
        return expect($(this.player)).toHandleWith('resize', this.caption.onWindowResize);
      });
      it('bind player updatePlayTime event', function() {
        return expect($(this.player)).toHandleWith('updatePlayTime', this.caption.onUpdatePlayTime);
      });
      it('bind the hide caption button', function() {
        return expect($('.hide-subtitles')).toHandleWith('click', this.caption.toggle);
      });
      return it('bind the mouse movement', function() {
        expect($('.subtitles')).toHandleWith('mouseenter', this.caption.onMouseEnter);
        expect($('.subtitles')).toHandleWith('mouseleave', this.caption.onMouseLeave);
        expect($('.subtitles')).toHandleWith('mousemove', this.caption.onMovement);
        expect($('.subtitles')).toHandleWith('mousewheel', this.caption.onMovement);
        return expect($('.subtitles')).toHandleWith('DOMMouseScroll', this.caption.onMovement);
      });
    });
    describe('mouse movement', function() {
      beforeEach(function() {
        spyOn(window, 'setTimeout').andReturn(100);
        spyOn(window, 'clearTimeout');
        return this.caption = new VideoCaption(this.player, 'def456');
      });
      describe('when cursor is outside of the caption box', function() {
        beforeEach(function() {
          return $(window).trigger(jQuery.Event('mousemove'));
        });
        return it('does not set freezing timeout', function() {
          return expect(this.caption.frozen).toBeFalsy();
        });
      });
      describe('when cursor is in the caption box', function() {
        beforeEach(function() {
          return $('.subtitles').trigger(jQuery.Event('mouseenter'));
        });
        it('set the freezing timeout', function() {
          return expect(this.caption.frozen).toEqual(100);
        });
        describe('when the cursor is moving', function() {
          beforeEach(function() {
            return $('.subtitles').trigger(jQuery.Event('mousemove'));
          });
          return it('reset the freezing timeout', function() {
            return expect(window.clearTimeout).toHaveBeenCalledWith(100);
          });
        });
        return describe('when the mouse is scrolling', function() {
          beforeEach(function() {
            return $('.subtitles').trigger(jQuery.Event('mousewheel'));
          });
          return it('reset the freezing timeout', function() {
            return expect(window.clearTimeout).toHaveBeenCalledWith(100);
          });
        });
      });
      return describe('when cursor is moving out of the caption box', function() {
        beforeEach(function() {
          this.caption.frozen = 100;
          return $.fn.scrollTo.reset();
        });
        describe('always', function() {
          beforeEach(function() {
            return $('.subtitles').trigger(jQuery.Event('mouseout'));
          });
          it('reset the freezing timeout', function() {
            return expect(window.clearTimeout).toHaveBeenCalledWith(100);
          });
          return it('unfreeze the caption', function() {
            return expect(this.caption.frozen).toBeNull();
          });
        });
        describe('when the player is playing', function() {
          beforeEach(function() {
            spyOn(this.player, 'isPlaying').andReturn(true);
            $('.subtitles li[data-index]:first').addClass('current');
            return $('.subtitles').trigger(jQuery.Event('mouseout'));
          });
          return it('scroll the caption', function() {
            return expect($.fn.scrollTo).toHaveBeenCalled();
          });
        });
        return describe('when the player is not playing', function() {
          beforeEach(function() {
            spyOn(this.player, 'isPlaying').andReturn(false);
            return $('.subtitles').trigger(jQuery.Event('mouseout'));
          });
          return it('does not scroll the caption', function() {
            return expect($.fn.scrollTo).not.toHaveBeenCalled();
          });
        });
      });
    });
    describe('search', function() {
      beforeEach(function() {
        return this.caption = new VideoCaption(this.player, 'def456');
      });
      return it('return a correct caption index', function() {
        expect(this.caption.search(0)).toEqual(0);
        expect(this.caption.search(9999)).toEqual(0);
        expect(this.caption.search(10000)).toEqual(1);
        expect(this.caption.search(15000)).toEqual(1);
        expect(this.caption.search(120000)).toEqual(12);
        return expect(this.caption.search(120001)).toEqual(12);
      });
    });
    describe('onUpdatePlayTime', function() {
      beforeEach(function() {
        return this.caption = new VideoCaption(this.player, 'def456');
      });
      describe('when the video speed is 1.0x', function() {
        beforeEach(function() {
          this.video.setSpeed('1.0');
          return this.caption.onUpdatePlayTime({}, 25.000);
        });
        return it('search the caption based on time', function() {
          return expect(this.caption.currentIndex).toEqual(2);
        });
      });
      describe('when the video speed is not 1.0x', function() {
        beforeEach(function() {
          this.video.setSpeed('0.75');
          return this.caption.onUpdatePlayTime({}, 25.000);
        });
        return it('search the caption based on 1.0x speed', function() {
          return expect(this.caption.currentIndex).toEqual(1);
        });
      });
      describe('when the index is not the same', function() {
        beforeEach(function() {
          this.caption.currentIndex = 1;
          $('.subtitles li[data-index=1]').addClass('current');
          return this.caption.onUpdatePlayTime({}, 25.000);
        });
        it('deactivate the previous caption', function() {
          return expect($('.subtitles li[data-index=1]')).not.toHaveClass('current');
        });
        it('activate new caption', function() {
          return expect($('.subtitles li[data-index=2]')).toHaveClass('current');
        });
        it('save new index', function() {
          return expect(this.caption.currentIndex).toEqual(2);
        });
        return it('scroll caption to new position', function() {
          return expect($.fn.scrollTo).toHaveBeenCalled();
        });
      });
      return describe('when the index is the same', function() {
        beforeEach(function() {
          this.caption.currentIndex = 1;
          $('.subtitles li[data-index=1]').addClass('current');
          return this.caption.onUpdatePlayTime({}, 15.000);
        });
        return it('does not change current subtitle', function() {
          return expect($('.subtitles li[data-index=1]')).toHaveClass('current');
        });
      });
    });
    describe('onWindowResize', function() {
      beforeEach(function() {
        this.caption = new VideoCaption(this.player, 'def456');
        $('.subtitles li[data-index=1]').addClass('current');
        return this.caption.onWindowResize();
      });
      it('set the height of caption container', function() {
        return expect(parseInt($('.subtitles').css('maxHeight'))).toEqual($('.video-wrapper').height());
      });
      it('set the height of caption spacing', function() {
        expect(parseInt($('.subtitles .spacing:first').css('height'))).toEqual($('.video-wrapper').height() / 2 - $('.subtitles li:not(.spacing):first').height() / 2);
        return expect(parseInt($('.subtitles .spacing:last').css('height'))).toEqual($('.video-wrapper').height() / 2 - $('.subtitles li:not(.spacing):last').height() / 2);
      });
      return it('scroll caption to new position', function() {
        return expect($.fn.scrollTo).toHaveBeenCalled();
      });
    });
    describe('scrollCaption', function() {
      beforeEach(function() {
        return this.caption = new VideoCaption(this.player, 'def456');
      });
      describe('when frozen', function() {
        beforeEach(function() {
          this.caption.frozen = true;
          $('.subtitles li[data-index=1]').addClass('current');
          return this.caption.scrollCaption();
        });
        return it('does not scroll the caption', function() {
          return expect($.fn.scrollTo).not.toHaveBeenCalled();
        });
      });
      return describe('when not frozen', function() {
        beforeEach(function() {
          return this.caption.frozen = false;
        });
        describe('when there is no current caption', function() {
          beforeEach(function() {
            return this.caption.scrollCaption();
          });
          return it('does not scroll the caption', function() {
            return expect($.fn.scrollTo).not.toHaveBeenCalled();
          });
        });
        return describe('when there is a current caption', function() {
          beforeEach(function() {
            $('.subtitles li[data-index=1]').addClass('current');
            return this.caption.scrollCaption();
          });
          return it('scroll to current caption', function() {
            return expect($.fn.scrollTo).toHaveBeenCalledWith($('.subtitles .current:first', this.player.element), {
              offset: -($('.video-wrapper').height() / 2 - $('.subtitles .current:first').height() / 2)
            });
          });
        });
      });
    });
    describe('seekPlayer', function() {
      beforeEach(function() {
        var _this = this;
        this.caption = new VideoCaption(this.player, 'def456');
        this.time = null;
        return $(this.player).bind('seek', function(event, time) {
          return _this.time = time;
        });
      });
      describe('when the video speed is 1.0x', function() {
        beforeEach(function() {
          this.video.setSpeed('1.0');
          return $('.subtitles li[data-start="30000"]').click();
        });
        return it('trigger seek event with the correct time', function() {
          return expect(this.time).toEqual(30.000);
        });
      });
      return describe('when the video speed is not 1.0x', function() {
        beforeEach(function() {
          this.video.setSpeed('0.75');
          return $('.subtitles li[data-start="30000"]').click();
        });
        return it('trigger seek event with the correct time', function() {
          return expect(this.time).toEqual(40.000);
        });
      });
    });
    return describe('toggle', function() {
      beforeEach(function() {
        this.caption = new VideoCaption(this.player, 'def456');
        return $('.subtitles li[data-index=1]').addClass('current');
      });
      describe('when the caption is visible', function() {
        beforeEach(function() {
          this.player.element.removeClass('closed');
          return this.caption.toggle(jQuery.Event('click'));
        });
        return it('hide the caption', function() {
          return expect(this.player.element).toHaveClass('closed');
        });
      });
      return describe('when the caption is hidden', function() {
        beforeEach(function() {
          this.player.element.addClass('closed');
          return this.caption.toggle(jQuery.Event('click'));
        });
        it('show the caption', function() {
          return expect(this.player.element).not.toHaveClass('closed');
        });
        return it('scroll the caption', function() {
          return expect($.fn.scrollTo).toHaveBeenCalled();
        });
      });
    });
  });

}).call(this);
