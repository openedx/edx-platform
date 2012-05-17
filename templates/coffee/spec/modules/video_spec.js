(function() {

  describe('Video', function() {
    beforeEach(function() {
      loadFixtures('video.html');
      return jasmine.stubRequests();
    });
    afterEach(function() {
      window.player = void 0;
      return window.onYouTubePlayerAPIReady = void 0;
    });
    describe('constructor', function() {
      beforeEach(function() {
        $.cookie.andReturn('0.75');
        return window.player = 100;
      });
      describe('by default', function() {
        beforeEach(function() {
          return this.video = new Video('example', '.75:abc123,1.0:def456');
        });
        it('reset the current video player', function() {
          return expect(window.player).toBeNull();
        });
        it('set the elements', function() {
          return expect(this.video.element).toBe('#video_example');
        });
        it('parse the videos', function() {
          return expect(this.video.videos).toEqual({
            '0.75': 'abc123',
            '1.0': 'def456'
          });
        });
        it('fetch the video metadata', function() {
          return expect(this.video.metadata).toEqual({
            abc123: {
              id: 'abc123',
              duration: 100
            },
            def456: {
              id: 'def456',
              duration: 200
            }
          });
        });
        it('parse available video speeds', function() {
          return expect(this.video.speeds).toEqual(['0.75', '1.0']);
        });
        it('set current video speed via cookie', function() {
          return expect(this.video.speed).toEqual('0.75');
        });
        return it('store a reference for this video player in the element', function() {
          return expect($('.video').data('video')).toEqual(this.video);
        });
      });
      describe('when the Youtube API is already available', function() {
        beforeEach(function() {
          this.originalYT = window.YT;
          window.YT = {
            Player: true
          };
          this.stubVideoPlayer = jasmine.createSpy('VideoPlayer');
          spyOn(window, 'VideoPlayer').andReturn(this.stubVideoPlayer);
          return this.video = new Video('example', '.75:abc123,1.0:def456');
        });
        afterEach(function() {
          return window.YT = this.originalYT;
        });
        return it('create the Video Player', function() {
          expect(window.VideoPlayer).toHaveBeenCalledWith(this.video);
          return expect(this.video.player).toEqual(this.stubVideoPlayer);
        });
      });
      describe('when the Youtube API is not ready', function() {
        beforeEach(function() {
          return this.video = new Video('example', '.75:abc123,1.0:def456');
        });
        return it('set the callback on the window object', function() {
          return expect(window.onYouTubePlayerAPIReady).toEqual(jasmine.any(Function));
        });
      });
      return describe('when the Youtube API becoming ready', function() {
        beforeEach(function() {
          this.stubVideoPlayer = jasmine.createSpy('VideoPlayer');
          spyOn(window, 'VideoPlayer').andReturn(this.stubVideoPlayer);
          this.video = new Video('example', '.75:abc123,1.0:def456');
          return window.onYouTubePlayerAPIReady();
        });
        return it('create the Video Player for all video elements', function() {
          expect(window.VideoPlayer).toHaveBeenCalledWith(this.video);
          return expect(this.video.player).toEqual(this.stubVideoPlayer);
        });
      });
    });
    describe('youtubeId', function() {
      beforeEach(function() {
        $.cookie.andReturn('1.0');
        return this.video = new Video('example', '.75:abc123,1.0:def456');
      });
      describe('with speed', function() {
        return it('return the video id for given speed', function() {
          expect(this.video.youtubeId('0.75')).toEqual('abc123');
          return expect(this.video.youtubeId('1.0')).toEqual('def456');
        });
      });
      return describe('without speed', function() {
        return it('return the video id for current speed', function() {
          return expect(this.video.youtubeId()).toEqual('def456');
        });
      });
    });
    describe('setSpeed', function() {
      beforeEach(function() {
        return this.video = new Video('example', '.75:abc123,1.0:def456');
      });
      describe('when new speed is available', function() {
        beforeEach(function() {
          return this.video.setSpeed('0.75');
        });
        it('set new speed', function() {
          return expect(this.video.speed).toEqual('0.75');
        });
        return it('save setting for new speed', function() {
          return expect($.cookie).toHaveBeenCalledWith('video_speed', '0.75', {
            expires: 3650,
            path: '/'
          });
        });
      });
      return describe('when new speed is not available', function() {
        beforeEach(function() {
          return this.video.setSpeed('1.75');
        });
        return it('set speed to 1.0x', function() {
          return expect(this.video.speed).toEqual('1.0');
        });
      });
    });
    return describe('getDuration', function() {
      beforeEach(function() {
        return this.video = new Video('example', '.75:abc123,1.0:def456');
      });
      return it('return duration for current video', function() {
        return expect(this.video.getDuration()).toEqual(200);
      });
    });
  });

}).call(this);
