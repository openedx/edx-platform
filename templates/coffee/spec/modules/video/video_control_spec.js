(function() {

  describe('VideoControl', function() {
    beforeEach(function() {
      return this.player = jasmine.stubVideoPlayer(this);
    });
    describe('constructor', function() {
      beforeEach(function() {
        return this.control = new VideoControl(this.player);
      });
      it('render the video controls', function() {
        return expect($('.video-controls').html()).toContain('<div class="slider"></div>\n<div>\n  <ul class="vcr">\n    <li><a class="video_control play">Play</a></li>\n    <li>\n      <div class="vidtime">0:00 / 0:00</div>\n    </li>\n  </ul>\n  <div class="secondary-controls">\n    <a href="#" class="add-fullscreen" title="Fill browser">Fill Browser</a>\n  </div>\n</div>');
      });
      it('bind player events', function() {
        expect($(this.player)).toHandleWith('play', this.control.onPlay);
        expect($(this.player)).toHandleWith('pause', this.control.onPause);
        return expect($(this.player)).toHandleWith('ended', this.control.onPause);
      });
      return it('bind the playback button', function() {
        return expect($('.video_control')).toHandleWith('click', this.control.togglePlayback);
      });
    });
    describe('onPlay', function() {
      beforeEach(function() {
        this.control = new VideoControl(this.player);
        return this.control.onPlay();
      });
      return it('switch playback button to play state', function() {
        expect($('.video_control')).not.toHaveClass('play');
        expect($('.video_control')).toHaveClass('pause');
        return expect($('.video_control')).toHaveHtml('Pause');
      });
    });
    describe('onPause', function() {
      beforeEach(function() {
        this.control = new VideoControl(this.player);
        return this.control.onPause();
      });
      return it('switch playback button to pause state', function() {
        expect($('.video_control')).not.toHaveClass('pause');
        expect($('.video_control')).toHaveClass('play');
        return expect($('.video_control')).toHaveHtml('Play');
      });
    });
    return describe('togglePlayback', function() {
      beforeEach(function() {
        return this.control = new VideoControl(this.player);
      });
      describe('when the video is playing', function() {
        beforeEach(function() {
          spyOn(this.player, 'isPlaying').andReturn(true);
          spyOnEvent(this.player, 'pause');
          return this.control.togglePlayback(jQuery.Event('click'));
        });
        return it('trigger the pause event', function() {
          return expect('pause').toHaveBeenTriggeredOn(this.player);
        });
      });
      return describe('when the video is paused', function() {
        beforeEach(function() {
          spyOn(this.player, 'isPlaying').andReturn(false);
          spyOnEvent(this.player, 'play');
          return this.control.togglePlayback(jQuery.Event('click'));
        });
        return it('trigger the play event', function() {
          return expect('play').toHaveBeenTriggeredOn(this.player);
        });
      });
    });
  });

}).call(this);
