describe "OmniPlayer", ->
  describe "#constructor", ->
    beforeEach ->
      @elementId = 'playerElement'
      @videoId = 'testId'
      @type = 'TEST'
      @height = '300'
      @width = '600'
      @startSeconds = '200'
      @endSeconds = '400'

      @player = new OmniPlayer
        elementId: @elementId
        videoId: @videoId
        type: @type
        height: @height
        width: @width
        startSeconds: @startSeconds
        endSeconds: @endSeconds

    it "sets the elementId to the given value", ->
      expect(@player.elementId).toEqual @elementId

    it "sets the videoId to the given value", ->
      expect(@player.videoId).toEqual @videoId

    it "sets the type to the given value", ->
      expect(@player.videoType).toEqual @type

    it "sets the height to the given value", ->
      expect(@player.height).toEqual @height

    it "sets the width to the given value", ->
      expect(@player.width).toEqual @width

    it "sets the startSeconds to the given value", ->
      expect(@player.startSeconds).toEqual @startSeconds

    it "sets the endSeconds to the given value", ->
      expect(@player.endSeconds).toEqual @endSeconds

    it 'should call #[_type].createPlayer', ->
      spyOn(OmniPlayer["_#{@type}"], 'createPlayer')
      @player2 = new OmniPlayer
        elementId: @elementId
        videoId: @videoId
        type: @type
        height: @height
        width: @width
        startSeconds: @startSeconds
        endSeconds: @endSeconds
      expect(OmniPlayer["_#{@type}"].createPlayer).toHaveBeenCalled()

  describe "instance with a type of 'YT'", ->
    beforeEach ->
      @elementId = 'playerElement'
      @videoId = 'testId'
      @type = 'YT'
      @height = '300'
      @width = '600'
      @startSeconds = '200'
      @endSeconds = '400'

    xdescribe 'window.onYouTubeIframeAPIReady', ->

    xdescribe '._YT.build', ->

    describe '._YT.setup', ->
      beforeEach ->
        # prevent createPlayer from being called and calling #YT.setup
        spyOn(OmniPlayer._YT, 'createPlayer')

        @player = new OmniPlayer
          elementId: @elementId
          videoId: @videoId
          type: @type
          height: @height
          width: @width
          startSeconds: @startSeconds
          endSeconds: @endSeconds

      it 'creates a script element', ->
        spyOn(document, 'createElement').andCallThrough()
        OmniPlayer._YT.setup()
        expect(document.createElement).toHaveBeenCalledWith("script")

      it 'gets the first script Tag', ->
        spyOn(document, 'getElementsByTagName').andCallThrough()
        OmniPlayer._YT.setup()
        expect(document.getElementsByTagName).toHaveBeenCalledWith("script")

    describe '#[_type].createPlayer', ->
      describe 'when OmniPlayer.loaded.YT is true', ->
        beforeEach ->
          OmniPlayer.loaded.YT = true

        it 'calls .YT.build', ->
          spyOn(OmniPlayer._YT, 'build')

          @player = new OmniPlayer
            elementId: @elementId
            videoId: @videoId
            type: @type
            height: @height
            width: @width
            startSeconds: @startSeconds
            endSeconds: @endSeconds

          expect(OmniPlayer._YT.build).toHaveBeenCalled()


      describe 'when OmniPlayer.loaded.YT is false', -> 
        beforeEach ->
          OmniPlayer.loaded.YT = false

        it "creates a new window function called 'onYouTubeIframeAPIReady'", ->
          @player = new OmniPlayer
            elementId: @elementId
            videoId: @videoId
            type: @type
            height: @height
            width: @width
            startSeconds: @startSeconds
            endSeconds: @endSeconds   

          expect(window.onYouTubeIframeAPIReady).toBeDefined()     

        it 'calls .YT.setup', ->
          spyOn(OmniPlayer._YT, 'setup')

          @player = new OmniPlayer
            elementId: @elementId
            videoId: @videoId
            type: @type
            height: @height
            width: @width
            startSeconds: @startSeconds
            endSeconds: @endSeconds

          expect(OmniPlayer._YT.setup).toHaveBeenCalled()          


