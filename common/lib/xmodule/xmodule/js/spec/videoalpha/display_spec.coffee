describe 'VideoAlpha', ->
  metadata =
    slowerSpeedYoutubeId:
      id: @slowerSpeedYoutubeId
      duration: 300
    normalSpeedYoutubeId:
      id: @normalSpeedYoutubeId
      duration: 200

  beforeEach ->
    jasmine.stubRequests()
    window.onTouchBasedDevice = jasmine.createSpy('onTouchBasedDevice').andReturn false
    @videosDefinition = '0.75:slowerSpeedYoutubeId,1.0:normalSpeedYoutubeId'
    @slowerSpeedYoutubeId = 'slowerSpeedYoutubeId'
    @normalSpeedYoutubeId = 'normalSpeedYoutubeId'

  afterEach ->
    window.OldVideoPlayerAlpha = undefined
    window.onYouTubePlayerAPIReady = undefined
    window.onHTML5PlayerAPIReady = undefined

  describe 'constructor', ->
    describe 'YT', ->
      beforeEach ->
        loadFixtures 'videoalpha.html'
        @stubVideoPlayerAlpha = jasmine.createSpy('VideoPlayerAlpha')
        $.cookie.andReturn '0.75'

      describe 'by default', ->
        beforeEach ->
          spyOn(window.VideoAlpha.prototype, 'fetchMetadata').andCallFake ->
            @metadata = metadata
          @video = new VideoAlpha '#example', @videosDefinition

        it 'check videoType', ->
          expect(@video.videoType).toEqual('youtube')

        it 'reset the current video player', ->
          expect(window.OldVideoPlayerAlpha).toBeUndefined()

        it 'set the elements', ->
          expect(@video.el).toBe '#video_id'

        it 'parse the videos', ->
          expect(@video.videos).toEqual
            '0.75': @slowerSpeedYoutubeId
            '1.0': @normalSpeedYoutubeId

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
          spyOn(window, 'VideoPlayerAlpha').andReturn(@stubVideoPlayerAlpha)
          @video = new VideoAlpha '#example', @videosDefinition

        afterEach ->
          window.YT = @originalYT

        it 'create the Video Player', ->
          expect(window.VideoPlayerAlpha).toHaveBeenCalledWith(video: @video)
          expect(@video.player).toEqual @stubVideoPlayerAlpha

      describe 'when the Youtube API is not ready', ->
        beforeEach ->
          @originalYT = window.YT
          window.YT = {}
          @video = new VideoAlpha '#example', @videosDefinition

        afterEach ->
          window.YT = @originalYT

        it 'set the callback on the window object', ->
          expect(window.onYouTubePlayerAPIReady).toEqual jasmine.any(Function)

      describe 'when the Youtube API becoming ready', ->
        beforeEach ->
          @originalYT = window.YT
          window.YT = {}
          spyOn(window, 'VideoPlayerAlpha').andReturn(@stubVideoPlayerAlpha)
          @video = new VideoAlpha '#example', @videosDefinition
          window.onYouTubePlayerAPIReady()

        afterEach ->
          window.YT = @originalYT

        it 'create the Video Player for all video elements', ->
          expect(window.VideoPlayerAlpha).toHaveBeenCalledWith(video: @video)
          expect(@video.player).toEqual @stubVideoPlayerAlpha

    describe 'HTML5', ->
      beforeEach ->
        loadFixtures 'videoalpha_html5.html'
        @stubVideoPlayerAlpha = jasmine.createSpy('VideoPlayerAlpha')
        $.cookie.andReturn '0.75'

      describe 'by default', ->
        beforeEach ->
          @originalHTML5 = window.HTML5Video.Player
          window.HTML5Video.Player = undefined
          @video = new VideoAlpha '#example', @videosDefinition

        afterEach ->
          window.HTML5Video.Player = @originalHTML5

        it 'check videoType', ->
          expect(@video.videoType).toEqual('html5')

        it 'reset the current video player', ->
          expect(window.OldVideoPlayerAlpha).toBeUndefined()

        it 'set the elements', ->
          expect(@video.el).toBe '#video_id'

        it 'parse the videos if subtitles exist', ->
          sub = 'test_name_of_the_subtitles'
          expect(@video.videos).toEqual
            '0.75': sub
            '1.0': sub
            '1.25': sub
            '1.5': sub

        it 'parse the videos if subtitles doesn\'t exist', ->
          $('#example').find('.video').data('sub', '')
          @video = new VideoAlpha '#example', @videosDefinition
          sub = ''
          expect(@video.videos).toEqual
            '0.75': sub
            '1.0': sub
            '1.25': sub
            '1.5': sub

        it 'parse Html5 sources', ->
          html5Sources =
            mp4: 'test.mp4'
            webm: 'test.webm'
            ogg: 'test.ogv'
          expect(@video.html5Sources).toEqual html5Sources

        it 'parse available video speeds', ->
          speeds = jasmine.stubbedHtml5Speeds
          expect(@video.speeds).toEqual speeds

        it 'set current video speed via cookie', ->
          expect(@video.speed).toEqual '0.75'

        it 'store a reference for this video player in the element', ->
          expect($('.video').data('video')).toEqual @video

      describe 'when the HTML5 API is already available', ->
        beforeEach ->
          @originalHTML5Video = window.HTML5Video
          window.HTML5Video = { Player: true }
          spyOn(window, 'VideoPlayerAlpha').andReturn(@stubVideoPlayerAlpha)
          @video = new VideoAlpha '#example', @videosDefinition

        afterEach ->
          window.HTML5Video = @originalHTML5Video

        it 'create the Video Player', ->
          expect(window.VideoPlayerAlpha).toHaveBeenCalledWith(video: @video)
          expect(@video.player).toEqual @stubVideoPlayerAlpha

      describe 'when the HTML5 API is not ready', ->
        beforeEach ->
          @originalHTML5Video = window.HTML5Video
          window.HTML5Video = {}
          @video = new VideoAlpha '#example', @videosDefinition

        afterEach ->
          window.HTML5Video = @originalHTML5Video

        it 'set the callback on the window object', ->
          expect(window.onHTML5PlayerAPIReady).toEqual jasmine.any(Function)

      describe 'when the HTML5 API becoming ready', ->
        beforeEach ->
          @originalHTML5Video = window.HTML5Video
          window.HTML5Video = {}
          spyOn(window, 'VideoPlayerAlpha').andReturn(@stubVideoPlayerAlpha)
          @video = new VideoAlpha '#example', @videosDefinition
          window.onHTML5PlayerAPIReady()

        afterEach ->
          window.HTML5Video = @originalHTML5Video

        it 'create the Video Player for all video elements', ->
          expect(window.VideoPlayerAlpha).toHaveBeenCalledWith(video: @video)
          expect(@video.player).toEqual @stubVideoPlayerAlpha

  describe 'youtubeId', ->
    beforeEach ->
      loadFixtures 'videoalpha.html'
      $.cookie.andReturn '1.0'
      @video = new VideoAlpha '#example', @videosDefinition

    describe 'with speed', ->
      it 'return the video id for given speed', ->
        expect(@video.youtubeId('0.75')).toEqual @slowerSpeedYoutubeId
        expect(@video.youtubeId('1.0')).toEqual @normalSpeedYoutubeId

    describe 'without speed', ->
      it 'return the video id for current speed', ->
        expect(@video.youtubeId()).toEqual @normalSpeedYoutubeId

  describe 'setSpeed', ->
    describe 'YT', ->
      beforeEach ->
        loadFixtures 'videoalpha.html'
        @video = new VideoAlpha '#example', @videosDefinition

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

    describe 'HTML5', ->
      beforeEach ->
        loadFixtures 'videoalpha_html5.html'
        @video = new VideoAlpha '#example', @videosDefinition

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
      loadFixtures 'videoalpha.html'
      @video = new VideoAlpha '#example', @videosDefinition

    it 'return duration for current video', ->
      expect(@video.getDuration()).toEqual 200

  describe 'log', ->
    beforeEach ->
      loadFixtures 'videoalpha.html'
      @video = new VideoAlpha '#example', @videosDefinition
      spyOn Logger, 'log'
      @video.log 'someEvent', {
        currentTime: 25,
        speed: '1.0'
      }

    it 'call the logger with valid extra parameters', ->
      expect(Logger.log).toHaveBeenCalledWith 'someEvent',
        id: 'id'
        code: @normalSpeedYoutubeId
        currentTime: 25
        speed: '1.0'
