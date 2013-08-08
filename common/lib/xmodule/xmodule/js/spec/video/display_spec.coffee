describe 'Video', ->
  metadata = undefined

  beforeEach ->
    loadFixtures 'video.html'
    jasmine.stubRequests()

    @['7tqY6eQzVhE'] = '7tqY6eQzVhE'
    @['cogebirgzzM'] = 'cogebirgzzM'
    metadata =
      '7tqY6eQzVhE':
        id: @['7tqY6eQzVhE']
        duration: 300
      'cogebirgzzM':
        id: @['cogebirgzzM']
        duration: 200

  afterEach ->
    window.player = undefined
    window.onYouTubePlayerAPIReady = undefined

  describe 'constructor', ->
    beforeEach ->
      @stubVideoPlayer = jasmine.createSpy('VideoPlayer')
      $.cookie.andReturn '0.75'
      window.player = undefined

    describe 'by default', ->
      beforeEach ->
        spyOn(window.Video.prototype, 'fetchMetadata').andCallFake ->
          @metadata = metadata
        @video = new Video '#example'
      it 'reset the current video player', ->
        expect(window.player).toBeNull()

      it 'set the elements', ->
        expect(@video.el).toBe '#video_id'

      it 'parse the videos', ->
        expect(@video.videos).toEqual
          '0.75': @['7tqY6eQzVhE']
          '1.0': @['cogebirgzzM']

      it 'fetch the video metadata', ->
        expect(@video.fetchMetadata).toHaveBeenCalled
        expect(@video.metadata).toEqual metadata

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
        @video = new Video '#example'

      afterEach ->
        window.YT = @originalYT

      it 'create the Video Player', ->
        expect(window.VideoPlayer).toHaveBeenCalledWith(video: @video)
        expect(@video.player).toEqual @stubVideoPlayer

    describe 'when the Youtube API is not ready', ->
      beforeEach ->
        @originalYT = window.YT
        window.YT = {}
        @video = new Video '#example'

      afterEach ->
        window.YT = @originalYT

      it 'set the callback on the window object', ->
        expect(window.onYouTubePlayerAPIReady).toEqual jasmine.any(Function)

    describe 'when the Youtube API becoming ready', ->
      beforeEach ->
        @originalYT = window.YT
        window.YT = {}
        spyOn(window, 'VideoPlayer').andReturn(@stubVideoPlayer)
        @video = new Video '#example'
        window.onYouTubePlayerAPIReady()

      afterEach ->
        window.YT = @originalYT

      it 'create the Video Player for all video elements', ->
        expect(window.VideoPlayer).toHaveBeenCalledWith(video: @video)
        expect(@video.player).toEqual @stubVideoPlayer

  describe 'youtubeId', ->
    beforeEach ->
      $.cookie.andReturn '1.0'
      @video = new Video '#example'

    describe 'with speed', ->
      it 'return the video id for given speed', ->
        expect(@video.youtubeId('0.75')).toEqual @['7tqY6eQzVhE']
        expect(@video.youtubeId('1.0')).toEqual @['cogebirgzzM']

    describe 'without speed', ->
      it 'return the video id for current speed', ->
        expect(@video.youtubeId()).toEqual @cogebirgzzM

  describe 'setSpeed', ->
    beforeEach ->
      @video = new Video '#example'

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
      @video = new Video '#example'

    it 'return duration for current video', ->
      expect(@video.getDuration()).toEqual 200

  describe 'log', ->
    beforeEach ->
      @video = new Video '#example'
      @video.setSpeed '1.0'
      spyOn Logger, 'log'
      @video.player = { currentTime: 25 }
      @video.log 'someEvent'

    it 'call the logger with valid parameters', ->
      expect(Logger.log).toHaveBeenCalledWith 'someEvent',
        id: 'id'
        code: @cogebirgzzM
        currentTime: 25
        speed: '1.0'
