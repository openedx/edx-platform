describe 'Video', ->
  beforeEach ->
    loadFixtures 'video.html'
    jasmine.stubRequests()

  afterEach ->
    window.player = undefined
    window.onYouTubePlayerAPIReady = undefined

  describe 'constructor', ->
    beforeEach ->
      @stubVideoPlayer = jasmine.createSpy('VideoPlayer')
      $.cookie.andReturn '0.75'
      window.player = 100

    describe 'by default', ->
      beforeEach ->
        @video = new Video 'example', '.75:abc123,1.0:def456'

      it 'reset the current video player', ->
        expect(window.player).toBeNull()

      it 'set the elements', ->
        expect(@video.element).toBe '#video_example'

      it 'parse the videos', ->
        expect(@video.videos).toEqual
          '0.75': 'abc123'
          '1.0': 'def456'

      it 'fetch the video metadata', ->
        expect(@video.metadata).toEqual
          abc123:
            id: 'abc123'
            duration: 100
          def456:
            id: 'def456'
            duration: 200

      it 'parse available video speeds', ->
        expect(@video.speeds).toEqual ['0.75', '1.0']

      it 'set current video speed via cookie', ->
        expect(@video.speed).toEqual '0.75'

      it 'store a reference for this video player in the element', ->
        expect($('.video').data('video')).toEqual @video

    describe 'when the Youtube API is already available', ->
      beforeEach ->
        @originalYT = window.YT
        window.YT = { Player: true }
        spyOn(window, 'VideoPlayer').andReturn(@stubVideoPlayer)
        @video = new Video 'example', '.75:abc123,1.0:def456'

      afterEach ->
        window.YT = @originalYT

      it 'create the Video Player', ->
        expect(window.VideoPlayer).toHaveBeenCalledWith @video
        expect(@video.player).toEqual @stubVideoPlayer

    describe 'when the Youtube API is not ready', ->
      beforeEach ->
        @originalYT = window.YT
        window.YT = {}
        @video = new Video 'example', '.75:abc123,1.0:def456'

      afterEach ->
        window.YT = @originalYT

      it 'set the callback on the window object', ->
        expect(window.onYouTubePlayerAPIReady).toEqual jasmine.any(Function)

    describe 'when the Youtube API becoming ready', ->
      beforeEach ->
        @originalYT = window.YT
        window.YT = {}
        spyOn(window, 'VideoPlayer').andReturn(@stubVideoPlayer)
        @video = new Video 'example', '.75:abc123,1.0:def456'
        window.onYouTubePlayerAPIReady()

      afterEach ->
        window.YT = @originalYT

      it 'create the Video Player for all video elements', ->
        expect(window.VideoPlayer).toHaveBeenCalledWith @video
        expect(@video.player).toEqual @stubVideoPlayer

  describe 'youtubeId', ->
    beforeEach ->
      $.cookie.andReturn '1.0'
      @video = new Video 'example', '.75:abc123,1.0:def456'

    describe 'with speed', ->
      it 'return the video id for given speed', ->
        expect(@video.youtubeId('0.75')).toEqual 'abc123'
        expect(@video.youtubeId('1.0')).toEqual 'def456'

    describe 'without speed', ->
      it 'return the video id for current speed', ->
        expect(@video.youtubeId()).toEqual 'def456'

  describe 'setSpeed', ->
    beforeEach ->
      @video = new Video 'example', '.75:abc123,1.0:def456'

    describe 'when new speed is available', ->
      beforeEach ->
        @video.setSpeed '0.75'

      it 'set new speed', ->
        expect(@video.speed).toEqual '0.75'

      it 'save setting for new speed', ->
        expect($.cookie).toHaveBeenCalledWith 'video_speed', '0.75', expires: 3650, path: '/'

    describe 'when new speed is not available', ->
      beforeEach ->
        @video.setSpeed '1.75'

      it 'set speed to 1.0x', ->
        expect(@video.speed).toEqual '1.0'

  describe 'getDuration', ->
    beforeEach ->
      @video = new Video 'example', '.75:abc123,1.0:def456'

    it 'return duration for current video', ->
      expect(@video.getDuration()).toEqual 200
