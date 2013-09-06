describe "VideoClipper", ->

  describe "when constructing", ->
    beforeEach ->
      @textareaId = 'bl-text'
      @videoId = '8f7wj_RcqYk'
      @videoType = 'TEST'

    afterEach ->
      VideoClipper.cleanUp()

    describe 'with defaults', ->
      beforeEach ->
        @clippy = new VideoClipper
          textareaId: @textareaId
          videoId: @videoId
          videoType: @videoType

      it "uses @textareaId for the instance's textareaId", ->
        expect(@clippy.textareaId).toEqual @textareaId

      it "uses @videoId for the instance's videoId", ->
        expect(@clippy.videoId).toEqual @videoId

      it "uses @videoType for the instance's videoType", ->
        expect(@clippy.videoType).toEqual @videoType

      it "uses VideoClipper.reel for the instance's reel", ->
        expect(@clippy.reel).toEqual VideoClipper.reel

      it "uses VideoClipper.answerClass for the instance's answerClass", ->
        expect(@clippy.answerClass).toEqual VideoClipper.answerClass

      it "uses VideoClipper.generateHtml for the instance's generate", ->
        expect(@clippy.generate).toEqual VideoClipper.generateHtml

      it 'generates a buttonId for the instance', ->
        expect(@clippy.buttonId).toBeDefined()

    describe 'without using defaults', ->
      beforeEach ->
        @answerClass = 'answer-class-test'
        @reel = 'reel-test'
        @buttonId = 'button-id-test'
        @textareaId = 'bl-text'
        @generate = false
        @mediaContentUrl = 'http://google.com'
        @thumbnailUrl = 'https://www.google.com/imghp?hl=en&tab=wi&authuser=0'

        @clippy = new VideoClipper
          textareaId: @textareaId
          videoId: @videoId
          videoType: @videoType
          generate: @generate
          reel: @reel
          buttonId: @buttonId
          answerClass: @answerClass
          mediaContentUrl: @mediaContentUrl
          thumbnailUrl: @thumbnailUrl

      it "uses @textareaId for the instance's textareaId", ->
        expect(@clippy.textareaId).toEqual @textareaId

      it "uses @videoId for the instance's videoId", ->
        expect(@clippy.videoId).toEqual @videoId

      it "uses @videoType for the instance's videoType", ->
        expect(@clippy.videoType).toEqual @videoType

      it "uses @mediaContentUrl for the instance's mediaContentUrl", ->
        expect(@clippy.mediaContentUrl).toEqual @mediaContentUrl

      it "uses @thumbnailUrl for the instance's thumbnailUrl", ->
        expect(@clippy.thumbnailUrl).toEqual @thumbnailUrl

      it "uses the given value for the instance's reel", ->
        expect(@clippy.reel).toEqual @reel

      it "uses the given value for the instance's answerClass", ->
        expect(@clippy.answerClass).toEqual @answerClass

      it "uses the given value for the instance's generate", ->
        expect(@clippy.generate).toEqual @generate

      it "uses the given value for the instance's buttonId", ->
        expect(@clippy.buttonId).toEqual @buttonId

    describe 'when generate is true', ->
      it 'calls #setup', ->
        # clippy.setup calls VideoClipper.generate, so
        # this tests spies on VideoClipper.generate
        spyOn(VideoClipper, 'generate')

        clippy = new VideoClipper
          textareaId: @textareaId
          videoId: @videoId
          videoType: @videoType
          generate: true

    describe 'when generate is false', ->
      it 'does not call #setup', ->
        # clippy.setup calls VideoClipper.generate, so
        # this tests spies on VideoClipper.generate
        spyOn(VideoClipper, 'generate')

        clippy = new VideoClipper
          textareaId: @textareaId
          videoId: @videoId
          videoType: @videoType
          generate: false

        expect(VideoClipper.generate).not.toHaveBeenCalled()

    it 'adds the new instance to VideoClipper.clippers', ->
      clippy = new VideoClipper
        textareaId: @textareaId
        videoId: @videoId
        videoType: @videoType
        generate: true

      addedClipper = false
      addedClipper = true for c in VideoClipper.clippers when c = clippy
      expect(addedClipper).toBeTruthy

  describe '.generateQuestionBox', ->
    beforeEach ->
      VideoClipper.cleanUp()
      loadFixtures('video_clipper_question.html')
      textareaId = 'bl-text'
      @selector = '#'+textareaId

      @clippy = new VideoClipper
        textareaId: textareaId
        videoId: '8f7wj_RcqYk'
        videoType: 'TEST'
        generate: false
        
    it 'gets the height of the element with textareaId', ->
      heightSpy = spyOn($.fn, 'height')
      spyOn(@clippy, 'generateQuestionBox').andCallThrough()
      @clippy.generateQuestionBox()
      expect(@clippy.generateQuestionBox).toHaveBeenCalled()
      expect($.fn.height).toHaveBeenCalled()
      expect(heightSpy.mostRecentCall.object.selector).toEqual(@selector)

    it 'gets the width of the element with textareaId', ->
      widthSpy = spyOn($.fn, 'width')
      @clippy.generateQuestionBox()
      expect($.fn.width).toHaveBeenCalled()
      expect(widthSpy.mostRecentCall.object.selector).toEqual @selector

    it 'gets the value of the element with textareaId', ->
      valSpy = spyOn $.fn, 'val'
      @clippy.generateQuestionBox()
      expect($.fn.val).toHaveBeenCalled()
      expect(valSpy.mostRecentCall.object.selector).toEqual @selector

    it 'inserts of an answerClass div after the textarea', ->
      @clippy.generateQuestionBox()
      textarea = $(@selector)
      expect(textarea.next()).toBe 'div'
      expect(textarea.next()).toHaveClass @clippy.answerClass

    it 'makes the divcontenteditable', ->
      @clippy.generateQuestionBox()
      textarea = $(@selector)
      expect(textarea.next()).toHaveAttr 'contenteditable', 'true'

    it 'makes the div have the same height and width as the textarea', ->
      @clippy.generateQuestionBox()
      textarea = $(@selector)
      div = textarea.next()
      expect(div.height()).toEqual textarea.height()
      expect(div.width()).toEqual textarea.width()

    it 'generates a bl data string', ->
      spyOn(VideoClipper, 'generateBLDataString')
      @clippy.generateQuestionBox()
      expect(VideoClipper.generateBLDataString).toHaveBeenCalledWith 'generate', @clippy

    describe 'without a buttonId specified', ->
      it 'creates a button after the outputbox div', ->
        @clippy.generateQuestionBox()
        div = $(@selector).next()
        expect(div.next()).toBe 'input[type=button]'

      it "sets the rel attribute of the button to 'blModal'", ->
        @clippy.generateQuestionBox()
        button = $(@selector).next().next()
        expect(button).toHaveAttr 'rel', 'blModal'

      it 'stores the encoded BLDataString in the bl-data attribute', ->
        @clippy.generateQuestionBox()
        button = $(@selector).next().next()

        blData = VideoClipper.generateBLDataString 'generate', @clippy

        encoded = encodeURI(blData)
        expect(button).toHaveAttr 'data-bl', encoded

      it 'makes the button respond to clicks', ->
        @clippy.generateQuestionBox()
        expect($("#"+@clippy.buttonId)).toHandle('click')

    describe 'with a buttonId specified', ->
      beforeEach ->
        @testID = "button-test"
        textareaId = 'bl-text'

        @clippy = new VideoClipper
          textareaId: textareaId
          videoId: '8f7wj_RcqYk'
          videoType: 'TEST'
          buttonId: @testID
          generate: false

      it "sets the rel attribute of the button to 'blModal'", ->
        @clippy.generateQuestionBox()
        button = $('#'+@testID)
        expect(button).toHaveAttr 'rel', 'blModal'

      it 'stores the encoded BLDataString in the bl-data attribute', ->
        @clippy.generateQuestionBox()
        button = $('#'+@testID)

        blData = VideoClipper.generateBLDataString 'generate', @clippy

        encoded = encodeURI(blData)
        expect(button).toHaveAttr 'data-bl', encoded

      it 'makes the button respond to clicks', ->
        @clippy.generateQuestionBox()
        expect($("#"+@clippy.buttonId)).toHandle('click')

  describe '.generateOverlay', ->
    beforeEach ->
      VideoClipper.cleanUp()
      loadFixtures('video_clipper_question.html')

      @clippy = new VideoClipper
        textareaId: 'bl-text'
        videoId: '8f7wj_RcqYk'
        videoType: 'TEST'
        generate: false

    it "creates a bookMarklet-overlay div if doesn't exist", ->
      expect($("#bookMarklet-overlay").length).toEqual 0
      appendSpy = spyOn($.fn, 'appendTo').andCallThrough()
      VideoClipper.generateOverlay()
      expect($("#bookMarklet-overlay").length).toEqual 1
      expect($.fn.appendTo).toHaveBeenCalled()

    describe 'and one already exists', ->

      it 'does not create another overlay', ->
        VideoClipper.generateOverlay()
        expect($("#bookMarklet-overlay").length).toEqual 1
        appendSpy = spyOn($.fn, 'appendTo').andCallThrough()
        VideoClipper.generateOverlay()
        expect($("#bookMarklet-overlay").length).toEqual 1
        expect($.fn.appendTo).not.toHaveBeenCalled()

    it 'makes the overlay respond to click', ->
      VideoClipper.generateOverlay()
      expect($("#bookMarklet-overlay")).toHandle('click')

    describe 'and the overlay is clicked', ->
      it 'calls modal.close', ->
        VideoClipper.generateOverlay()
        spyOn(VideoClipper.modal, "close").andCallThrough
        $("#bookMarklet-overlay").click()
        expect(VideoClipper.modal.close).toHaveBeenCalled()

  describe ".generateSnippetBox", ->
    beforeEach ->
      VideoClipper.cleanUp()
      loadFixtures('video_clipper_question.html')
      @testID = "button-test"
      textareaId = 'bl-text'

      @clippy = new VideoClipper
        textareaId: textareaId
        videoId: '8f7wj_RcqYk'
        videoType: 'TEST'
        buttonId: @testID
        generate: true

      VideoClipper.player = new OmniPlayer
        type: "TEST"

      VideoClipper.clipper = @clippy

    it "makes the start button respond to clicks", ->
      expect($('.bl-start')).toHandle("click")

    describe "and the start button is clicked", ->
  
      it "gets the current time from the player", ->
        spyOn(VideoClipper.player, 'getCurrentTime').andCallThrough()
        spyOn(VideoClipper, 'checkErrors')
        $('.bl-start').click()
        expect(VideoClipper.player.getCurrentTime).toHaveBeenCalled()

      it "sets the bl-start input to the current time", ->
        val = 300
        spyOn(VideoClipper.player, 'getCurrentTime').andReturn(val)
        spyOn(VideoClipper, 'checkErrors')
        inputSelector = "input[name='bl-start']"
        valSpy = spyOn($.fn, 'val').andCallThrough()
        $('.bl-start').click()
        expect($.fn.val).toHaveBeenCalledWith(VideoClipper.secondsToTime(val))
        expect(valSpy.mostRecentCall.object.selector).toEqual inputSelector

      it "checks for errors", ->
        spyOn(VideoClipper, 'checkErrors')
        $('.bl-start').click()
        expect(VideoClipper.checkErrors).toHaveBeenCalled()


    it "makes the end button respond to clicks", ->
      expect($('.bl-end')).toHandle("click")

    describe 'and end button is clicked', ->
      it "gets the current time from the player", ->
        spyOn(VideoClipper.player, 'getCurrentTime').andCallThrough()
        spyOn(VideoClipper, 'checkErrors')
        $('.bl-end').click()
        expect(VideoClipper.player.getCurrentTime).toHaveBeenCalled()

      it "sets the bl-start input to the current time", ->
        val = 300
        spyOn(VideoClipper.player, 'getCurrentTime').andReturn(val)
        spyOn(VideoClipper, 'checkErrors')
        inputSelector = "input[name='bl-end']"
        valSpy = spyOn($.fn, 'val').andCallThrough()
        $('.bl-end').click()
        expect($.fn.val).toHaveBeenCalledWith(VideoClipper.secondsToTime(val))
        expect(valSpy.mostRecentCall.object.selector).toEqual inputSelector

      it "checks for errors", ->
        spyOn(VideoClipper, 'checkErrors')
        $('.bl-end').click()
        expect(VideoClipper.checkErrors).toHaveBeenCalled()

    it "makes the reset button respond to clicks", ->
      expect($(".bl-reset")).toHandle("click")

    describe 'and the reset button is clicked', ->
      it 'clears the snippet box inputs', ->
        spyOn(VideoClipper, 'clearInputs')
        $('.bl-reset').click()
        expect(VideoClipper.clearInputs).toHaveBeenCalled

      it 'cues the video by id', ->
        spyOn(VideoClipper.player, 'cueVideoById')
        $('.bl-reset').click()
        expect(VideoClipper.player.cueVideoById).toHaveBeenCalled()

    it "makes the done button respond to clicks", ->
      expect($('.bl-done')).toHandle("click")

    describe 'and the done button is clicked', ->
      it 'closes the modal', ->
        spyOn(VideoClipper.modal, 'close')
        $('.bl-done').click()
        expect(VideoClipper.modal.close).toHaveBeenCalled()

      it 'generates a new tag', ->
        spyOn(VideoClipper, 'generateTag')
        $('.bl-done').click()
        expect(VideoClipper.generateTag).toHaveBeenCalled()

      it 'uses the generated tag to update', ->
        testString = 'Testing 1 2 3'
        spyOn(VideoClipper, 'generateTag').andReturn(testString)
        spyOn(@clippy, 'update')
        $('.bl-done').click()
        expect(@clippy.update).toHaveBeenCalledWith(testString)

    it 'sets VideoClipper prepared snippet to true', ->
      expect(VideoClipper.prepared.snippet).toBeTruthy()

  describe ".generateVideoBox", ->
    describe 'with a #bl-vid already', ->
      beforeEach ->
        VideoClipper.generateVideoBox()

      afterEach ->
        VideoClipper.cleanUp()
      it "does not add another #bl-vid div", ->
        expect($('#bl-vid').length).toEqual 1
        VideoClipper.generateVideoBox()
        expect($('#bl-vid').length).toEqual 1

    describe 'without a #bl-vid already', ->
      it 'adds a #bl-vid div', ->
        expect($('#bl-vid').length).toEqual 0
        VideoClipper.generateVideoBox()
        expect($('#bl-vid').length).toEqual 1

      it 'has #bl-playerV inside #bl-vid', ->
        VideoClipper.generateVideoBox()
        expect($('#bl-vid').find('#bl-playerV').length).toEqual 1        

    it 'returns VideoClipper', ->
      result = VideoClipper.generateVideoBox()
      expect(result).toEqual VideoClipper

  describe "#setup", ->
    beforeEach ->
      VideoClipper.cleanUp()
      loadFixtures('video_clipper_question.html')
      @testID = "button-test"
      textareaId = 'bl-text'

      @clippy = new VideoClipper
        textareaId: textareaId
        videoId: '8f7wj_RcqYk'
        videoType: 'TEST'
        buttonId: @testID
        generate: false

    it "generates a video box", ->
      expect($('#bl-vid').length).toBe(0)
      spyOn(VideoClipper, 'generateVideoBox')
      @clippy.setup()
      expect(VideoClipper.generateVideoBox).toHaveBeenCalled()

    it "generates a snippet box", ->
      expect($('#bl').length).toBe(0)
      spyOn(VideoClipper, 'generateSnippetBox')
      @clippy.setup()
      expect(VideoClipper.generateSnippetBox).toHaveBeenCalled()

    it "generates the question box", ->
      spyOn(@clippy, 'generateQuestionBox').andCallThrough()
      spyOn(VideoClipper, 'generateSnippetBox')
      @clippy.setup()
      expect(@clippy.generateQuestionBox).toHaveBeenCalled()

    it "generates the video clipper overlay", ->
      expect($('#bookmarklet-overlay').length).toBe(0)
      spyOn(VideoClipper, 'generateOverlay')
      @clippy.setup()
      expect(VideoClipper.generateOverlay).toHaveBeenCalled()

    describe 'with a valid output box', ->
      beforeEach ->
        onSpy = spyOn($.fn,'on').andCallThrough()
        @clippy.setup()

      it 'makes the output box respond to clicks', ->
        expect($("."+@clippy.answerClass)).toHandle('click')

      it 'makes the output box respond to keyups', ->
        expect($("."+@clippy.answerClass)).toHandle('keyup')

  describe '.generate', ->
    beforeEach ->
      VideoClipper.cleanUp()
      loadFixtures('video_clipper_question.html')
      @testID = "button-test"
      textareaId = 'bl-text'

      @clippy = new VideoClipper
        textareaId: textareaId
        videoId: '8f7wj_RcqYk'
        videoType: 'TEST'
        buttonId: @testID
        generate: false

    describe 'with a VideoClipper instance', ->
      beforeEach ->
        @clippy.generateQuestionBox()
        loadFixtures('video_clipper_question.html')

      it "generates a snippet box", ->
        expect($('#bl').length).toBe(0)
        spyOn(VideoClipper, 'generateSnippetBox')
        VideoClipper.generate @clippy
        expect(VideoClipper.generateSnippetBox).toHaveBeenCalledWith @clippy

      it "generates the video clipper overlay", ->
        expect($('#bookmarklet-overlay').length).toBe(0)
        spyOn(VideoClipper, 'generateOverlay')
        VideoClipper.generate @clippy
        expect(VideoClipper.generateOverlay).toHaveBeenCalled()

      it "generates a video box", ->
        expect($('#bl-vid').length).toBe(0)
        spyOn(VideoClipper, 'generateVideoBox')
        VideoClipper.generate @clippy
        expect(VideoClipper.generateVideoBox).toHaveBeenCalled()

    describe 'without a VideoClipper instance', ->
      beforeEach ->
        loadFixtures('video_clipper_answer.html')
      it "does not generate a snippet box", ->
        expect($('#bl').length).toBe(0)
        spyOn(VideoClipper, 'generateSnippetBox')
        VideoClipper.generate()
        expect($('#bl').length).toBe(0)
        expect(VideoClipper.generateSnippetBox).not.toHaveBeenCalled()

      it "generates the video clipper overlay", ->
        expect($('#bookmarklet-overlay').length).toBe(0)
        spyOn(VideoClipper, 'generateOverlay')
        VideoClipper.generate()
        expect(VideoClipper.generateOverlay).toHaveBeenCalled()

      it "generates a video box", ->
        expect($('#bl-vid').length).toBe(0)
        spyOn(VideoClipper, 'generateVideoBox')
        VideoClipper.generate()
        expect(VideoClipper.generateVideoBox).toHaveBeenCalled()

      it "makes video clips handle clicks", ->
        VideoClipper.generate()
        expect($('[rel*=blModal]')).toHandle 'click'

      it "adds a qtip to each '[rel*=blModal]'", ->
        VideoClipper.generate()
        expect($.fn.qtip).toHaveBeenCalled()

      describe 'when a video clip is click', ->
        it 'opens the modal window', ->
          spyOn(VideoClipper.modal, 'open')
          VideoClipper.generate()
          $('[rel*=blModal]').click()
          expect(VideoClipper.modal.open).toHaveBeenCalled()

  describe '.cleanUp', ->
    beforeEach ->
      VideoClipper.cleanUp()
      loadFixtures('video_clipper_question.html')
      @testID = "button-test"
      textareaId = 'bl-text'

      @clippy = new VideoClipper
        textareaId: textareaId
        videoId: '8f7wj_RcqYk'
        videoType: 'TEST'
        buttonId: @testID

    it 'removes the div with id of bl', ->
      expect($('#bl')).toExist()
      VideoClipper.cleanUp()
      expect($('#bl')).not.toExist()

    it 'removes the div with id of bl-vid', ->
      expect($('#bl-vid')).toExist()
      VideoClipper.cleanUp()
      expect($('#bl-vid')).not.toExist()

    it 'removes the div with id of bookMarklet-overlay', ->
      expect($('#bookMarklet-overlay')).toExist()
      VideoClipper.cleanUp()
      expect($('#bookMarklet-overlay')).not.toExist()

    it 'sets VideoClipper prepared snippet to false', ->
      VideoClipper.cleanUp()
      expect(VideoClipper.prepared.snippet).toBeFalsy()

    it 'removes all questionBoxs', ->
      spyOn(@clippy, 'destroy')
      VideoClipper.cleanUp()
      expect(@clippy.destroy).toHaveBeenCalled()

  describe ".modal.close", ->
    beforeEach ->
      VideoClipper.cleanUp()
      loadFixtures('video_clipper_question.html')
      @testID = "button-test"
      textareaId = 'bl-text'

      @clippy = new VideoClipper
        textareaId: textareaId
        videoId: '8f7wj_RcqYk'
        videoType: 'TEST'
        buttonId: @testID

      VideoClipper.modal.open $('#'+@testID), @clippy

    it "fades out the overlay", ->
      fadeSpy = spyOn($.fn, 'fadeOut')
      VideoClipper.modal.close(@clippy.modalID)
      expect($.fn.fadeOut).toHaveBeenCalled()
      expect(fadeSpy.mostRecentCall.object.selector).toEqual "#bookMarklet-overlay"

    it "hides the modal window", ->
      expect($("##{VideoClipper.modal.Id}")).toBeVisible()
      VideoClipper.modal.close()
      expect($("##{VideoClipper.modal.Id}")).toBeHidden()

    it "stops the video player", ->
      spyOn(VideoClipper.player, 'stopVideo')
      VideoClipper.modal.close(@clippy.modalID)
      expect(VideoClipper.player.stopVideo).toHaveBeenCalled()

  describe ".modal.open", ->
    beforeEach ->
      VideoClipper.cleanUp()
      loadFixtures('video_clipper_question.html')
      @testID = "button-test"
      textareaId = 'bl-text'

      @clippy = new VideoClipper
        textareaId: textareaId
        videoId: '8f7wj_RcqYk'
        videoType: 'TEST'
        buttonId: @testID

      @el = $('#'+@testID)
      @blData = VideoClipper.getBLData @el

    afterEach ->
      VideoClipper.modal.close()

    it 'closes any open modal windows', ->
      spyOn(VideoClipper.modal, 'close')
      VideoClipper.modal.open @el, @clippy
      expect(VideoClipper.modal.close).toHaveBeenCalled()

    it "gets the data from the element", ->
      spyOn(VideoClipper, 'getBLData').andReturn @blData
      VideoClipper.modal.open @el, @clippy
      expect(VideoClipper.getBLData).toHaveBeenCalledWith @el

    describe "with a snippet box", ->
      beforeEach ->
        spyOn(VideoClipper, 'getBLData').andReturn @blData

      it "gets video type and id", ->
        VideoClipper.modal.open @el, @clippy
        expect(@clippy.videoId).toEqual @blData.videoId
        expect(@clippy.videoType).toEqual @blData.videoType

      it "clears inputs", ->
        spyOn(VideoClipper, 'clearInputs').andCallThrough()
        VideoClipper.modal.open @el, @clippy
        expect(VideoClipper.clearInputs).toHaveBeenCalled()

      it "creates a video player if it doesn't exist", ->
        VideoClipper.modal.open @el, @clippy
        expect(VideoClipper.player).toEqual jasmine.any(OmniPlayer)

      it "shows snippet box", ->
        fadeSpy = spyOn($.fn,'fadeTo').andCallThrough()
        VideoClipper.modal.open @el, @clippy
        expect($.fn.fadeTo).toHaveBeenCalled()
        expect(fadeSpy.mostRecentCall.object.selector).toEqual('#bl')

      it "shows overlay", ->
        fadeSpy = spyOn($.fn,'fadeTo').andCallThrough()
        VideoClipper.modal.open @el, @clippy
        expect($.fn.fadeTo).toHaveBeenCalled()
        expect(fadeSpy.calls[0].object.selector).toEqual('#bookMarklet-overlay')

    describe "with a video box", ->
      beforeEach ->
        @clippy.startTime = '200'
        @clippy.endTime = '300'
        @blData = $.parseJSON VideoClipper.generateBLDataString('show', @clippy)
        spyOn(VideoClipper, 'getBLData').andReturn @blData

      afterEach ->
        VideoClipper.modal.close()

      it "gets video type, id, start time and end time", ->
        VideoClipper.modal.open @el
        expect(@clippy.videoId).toEqual @blData.videoId
        expect(@clippy.videoType).toEqual @blData.videoType
        expect(@clippy.startTime).toEqual @blData.startSeconds
        expect(@clippy.endTime).toEqual @blData.endSeconds

      it "creates a video player if it doesn't exist", ->
        VideoClipper.modal.open @el
        expect(VideoClipper.playerV).toEqual jasmine.any(OmniPlayer)

      it "shows video box", ->
        fadeSpy = spyOn($.fn,'fadeTo').andCallThrough()
        VideoClipper.modal.open @el
        expect($.fn.fadeTo).toHaveBeenCalled()
        expect(fadeSpy.mostRecentCall.object.selector).toEqual('#bl-vid')

      it "shows overlay", ->
        fadeSpy = spyOn($.fn,'fadeTo').andCallThrough()
        VideoClipper.modal.open @el
        expect($.fn.fadeTo).toHaveBeenCalled()
        expect(fadeSpy.calls[0].object.selector).toEqual('#bookMarklet-overlay')

  describe ".checkErrors", ->
    beforeEach ->
      VideoClipper.cleanUp()
      loadFixtures('video_clipper_question.html')
      @testID = "button-test"
      textareaId = 'bl-text'

      @clippy = new VideoClipper
        textareaId: textareaId
        videoId: '8f7wj_RcqYk'
        videoType: 'TEST'
        buttonId: @testID

    it "parses floats from the  start input box", ->
      $("input[name='bl-start']").val("300")
      spyOn(window, 'parseFloat').andReturn 300
      VideoClipper.checkErrors()
      expect(window.parseFloat).toHaveBeenCalledWith "300"

    it "parses floats from the  end input box", ->
      $("input[name='bl-end']").val("300")
      spyOn(window, 'parseFloat').andReturn 300
      VideoClipper.checkErrors()
      expect(window.parseFloat).toHaveBeenCalledWith "300"

    describe 'if correct', ->
      beforeEach ->
        $("input[name='bl-start']").val("300")
        $("input[name='bl-end']").val("400")

      it "removes incorrect highlighting class", ->
        $("input[name='bl-start']").addClass "bl-incorrect"
        $("input[name='bl-end']").addClass "bl-incorrect"
        VideoClipper.checkErrors()
        expect($("input[name='bl-start']")).not.toHaveClass "bl-incorrect"
        expect($("input[name='bl-end']")).not.toHaveClass "bl-incorrect"

      it "returns true", ->
        expect(VideoClipper.checkErrors()).toBeTruthy()      

    describe 'if incorrect', ->
      beforeEach ->
        $("input[name='bl-start']").val("400")
        $("input[name='bl-end']").val("300")

      it "adds incorrect highlighting class", -> 
        VideoClipper.checkErrors()
        expect($("input[name='bl-start']")).toHaveClass "bl-incorrect"
        expect($("input[name='bl-end']")).toHaveClass "bl-incorrect"

      it 'returns false', ->
        expect(VideoClipper.checkErrors()).toBeFalsy() 

  describe ".getBLData", ->
    beforeEach ->
      VideoClipper.cleanUp()
      loadFixtures('video_clipper_question.html')
      @testID = "button-test"
      textareaId = 'bl-text'

      @clippy = new VideoClipper
        textareaId: textareaId
        videoId: '8f7wj_RcqYk'
        videoType: 'TEST'
        buttonId: @testID

      @testDataGenerate = encodeURI VideoClipper.generateBLDataString('generate', @clippy)

      @clippy.startTime = '200'
      @clippy.endTime = '300'
      @testDataShow = encodeURI VideoClipper.generateBLDataString('show', @clippy)
      
      $('body').append("<div id='test'></div>")

    afterEach ->
      $('#test').remove()

    it "checks if it has a data-bl attribute", ->
      el = $('#test').attr('data-bl', @testDataGenerate)
      attrSpy = spyOn($.fn, 'attr').andCallThrough()
      VideoClipper.getBLData(el)
      expect($.fn.attr).toHaveBeenCalledWith('data-bl')
      expect(attrSpy.calls[0].object).toEqual(el)

    describe "with a data-bl attribute", ->
      beforeEach ->
        @el = $('#test').attr 'data-bl', @testDataGenerate

      it 'gets the encoded data from the data-bl attribute', ->
        attrSpy = spyOn($.fn, 'attr').andCallThrough()
        VideoClipper.getBLData @el
        expect($.fn.attr.calls.length).toEqual 2
        expect(attrSpy.calls[1].object).toEqual @el

      it "parses a JSON object from the data-bl attribute", ->
        spyOn($, 'parseJSON')
        VideoClipper.getBLData @el
        expect($.parseJSON).toHaveBeenCalledWith decodeURI @testDataGenerate

      it "produces a valid JSON object with the correct data", ->
        blData = VideoClipper.getBLData @el
        expect(blData).toEqual $.parseJSON decodeURI @testDataGenerate

    describe "without a data-bl attribute", ->
      beforeEach ->
        @el = $('#test').text @testDataShow

      it 'gets the encoded data from the elements tesxt', ->
        textSpy = spyOn($.fn, 'text').andCallThrough()
        VideoClipper.getBLData @el
        expect($.fn.text).toHaveBeenCalled()
        expect(textSpy.calls[0].object).toEqual(@el)

      it "parses a JSON object from the elements text", ->
        spyOn($, 'parseJSON')
        VideoClipper.getBLData @el
        expect($.parseJSON).toHaveBeenCalledWith decodeURI @testDataShow

      it "produces a valid JSON object with the correct data", ->
        blData = VideoClipper.getBLData @el
        expect(blData).toEqual $.parseJSON decodeURI @testDataShow


  describe ".clearInputs", ->
    beforeEach ->
      VideoClipper.cleanUp()
      loadFixtures('video_clipper_question.html')
      @testID = "button-test"
      textareaId = 'bl-text'

      @clippy = new VideoClipper
        textareaId: textareaId
        videoId: '8f7wj_RcqYk'
        videoType: 'TEST'
        buttonId: @testID

    it "clears values for input box in the snippet box", ->
      $("input[name='bl-end']").val 200
      $("input[name='bl-start']").val 300
      VideoClipper.clearInputs()
      expect($("input[name='bl-end']").val()).toEqual ""
      expect($("input[name='bl-start']").val()).toEqual ""      

    it "removes the bl-incorrect class from the input boxes", ->
      $("input[name='bl-end']").addClass "bl-incorrect"
      $("input[name='bl-start']").addClass "bl-incorrect"
      VideoClipper.clearInputs()
      expect($("input[name='bl-start']")).not.toHaveClass "bl-incorrect"
      expect($("input[name='bl-end']")).not.toHaveClass "bl-incorrect"

  describe "#update", -> 
    beforeEach ->
      VideoClipper.cleanUp()
      loadFixtures('video_clipper_question.html')
      @testID = "button-test"
      textareaId = 'bl-text'

      @clippy = new VideoClipper
        textareaId: textareaId
        videoId: '8f7wj_RcqYk'
        videoType: 'TEST'
        buttonId: @testID

      @clippy.startTime = '300'
      @clippy.endTime = '400'

      data = encodeURI VideoClipper.generateBLDataString('show',@clippy)

      @newTag = $("<a rel='blModal' href='#bl-vid' class='bl'>"+data+"</a>").
        css
          'background-image': @reel

      $('body').append("<div id='test'></div>")

    afterEach ->
      $('#test').remove()

    it "gets the question's current contents", ->
      contentSpy = spyOn($.fn, 'contents').andCallThrough()
      @clippy.update(@newTag)
      expect($.fn.contents).toHaveBeenCalled()
      expect(contentSpy.mostRecentCall.object).
        toEqual @clippy.questionBox

    describe "that doesn't already have contents", ->
      it "makes the div's text equal the new link", ->
        expect($('.'+@clippy.answerClass).contents().length).toEqual 0
        @clippy.update(@newTag)
        expect($('.'+@clippy.answerClass).find('a').text()).
          toEqual @newTag.text()

    describe 'that already has contents', ->
      it 'gets the questionBox contents', ->
          spyOn(@clippy.questionBox, 'contents').andCallThrough()
          @clippy.update(@newTag)
          expect(@clippy.questionBox.contents).toHaveBeenCalled()

      it "iterates through the question's text and html", ->
        eachAgent = jasmine.createSpyObj('each', ['each'])
        spyOn(@clippy.questionBox, 'contents').andReturn eachAgent
        @clippy.update(@newTag)
        expect(eachAgent.each).toHaveBeenCalled()

    it "updates the question's textarea", ->
      valSpy = spyOn($.fn, 'val').andCallThrough()
      @clippy.update(@newTag) 
      newVal = @clippy.questionBox.html()
      expect($.fn.val).toHaveBeenCalledWith newVal
      expect(valSpy.mostRecentCall.object).toEqual @clippy.questionBox.prev()

    it "makes video clips handle clicks", ->
      @clippy.update(@newTag)
      expect(@clippy.questionBox.find('[rel*=blModal]')).toHandle 'click'

    it "adds a qtip to each '[rel*=blModal]'", ->
      @clippy.update(@newTag)
      expect($.fn.qtip).toHaveBeenCalled()

    describe 'when a video clip is click', ->
      it 'opens the modal window', ->
        spyOn(VideoClipper.modal, 'open')
        @clippy.update(@newTag)
        $('[rel*=blModal]').click()
        expect(VideoClipper.modal.open).toHaveBeenCalled()

  describe ".generateTag", ->
    beforeEach ->
      VideoClipper.cleanUp()
      loadFixtures('video_clipper_question.html')
      @testID = "button-test"
      textareaId = 'bl-text'

      @clippy = new VideoClipper
        textareaId: textareaId
        videoId: '8f7wj_RcqYk'
        videoType: 'TEST'
        buttonId: @testID

      @el = $('#'+@testID)
      @blData = VideoClipper.getBLData @el

      VideoClipper.modal.open @el, @clippy

    afterEach ->
      VideoClipper.modal.close()

    it "gets start time from the snippet box", ->
      $("input[name='bl-start']").val("200.50")
      valSpy = spyOn($.fn, "val").andCallThrough()
      VideoClipper.generateTag @clippy
      expect($.fn.val).toHaveBeenCalled()
      expect("#{@clippy.startTime}").toEqual '200.50'
      expect(valSpy.calls[0].object.selector).toEqual("input[name='bl-start']")

    it "gets end time from the snippet box", ->
      $("input[name='bl-end']").val("300.50")
      valSpy = spyOn($.fn, "val").andCallThrough()
      VideoClipper.generateTag @clippy
      expect($.fn.val).toHaveBeenCalled()
      expect("#{@clippy.endTime}").toEqual '300.50'
      expect(valSpy.calls[1].object.selector).toEqual("input[name='bl-end']")

    it "checks for errors in the start and end times", ->
      spyOn(VideoClipper, 'checkErrors').andCallThrough()
      VideoClipper.generateTag @clippy
      expect(VideoClipper.checkErrors).toHaveBeenCalled()

    describe "with correct values", ->
      beforeEach ->
        $("input[name='bl-start']").val("200.50")
        $("input[name='bl-end']").val("300.50")
  
      it "sets the endTime to the video duration if it isn't defined", ->
        $("input[name='bl-end']").val("")
        spyOn(VideoClipper.player, 'getDuration').andReturn 400
        VideoClipper.generateTag @clippy
        expect(VideoClipper.player.getDuration).toHaveBeenCalled()

      it "generates a show data JSON string", ->
        spyOn(VideoClipper, 'generateBLDataString').andCallThrough()
        VideoClipper.generateTag @clippy
        expect(VideoClipper.generateBLDataString).toHaveBeenCalled()

      it "encodes the data string", ->
        spyOn(window, 'encodeURI')
        str = 'Test'
        spyOn(VideoClipper, 'generateBLDataString').andReturn (str)
        VideoClipper.generateTag @clippy
        expect(window.encodeURI).toHaveBeenCalledWith(str)
  

      it "creates an a tag with the encodedData in the text", ->
        str = 'Test'
        spyOn(VideoClipper, 'generateBLDataString').andReturn (str)
        tag = VideoClipper.generateTag @clippy
        expect(tag).toBe 'a'
        expect(tag.text()).toEqual encodeURI str

      it "adds the clip to the instance's clips", ->
        tag = VideoClipper.generateTag @clippy
        clipAdded = false
        clipAdded = true for clip in @clippy.clips when clip == tag
        expect(clipAdded).toBeTruthy

      it "returns the tag", ->
        tag = VideoClipper.generateTag @clippy
        expect(tag).toBe 'a'

    describe "without correct values", ->

      it "returns and empty string", ->
        spyOn(VideoClipper, 'checkErrors').andReturn false
        expect(VideoClipper.generateTag(@clippy)).toEqual ""  

  describe ".generateBLDataString", ->
    beforeEach -> 
      VideoClipper.cleanUp()
      loadFixtures('video_clipper_question.html')
      @testID = "button-test"
      textareaId = 'bl-text'
      @vid = '8f7wj_RcqYk'
      @videoType = 'TEST'

      @clippy = new VideoClipper
        textareaId: textareaId
        videoId: @vid
        videoType: @videoType
        buttonId: @testID

    describe "with a type of 'generate' ", ->
      beforeEach ->
        dataString = VideoClipper.generateBLDataString 'generate', @clippy
        @blData = $.parseJSON dataString

      it 'uses the vid of the instance in the JSON string', ->
        expect(@blData.videoId).toEqual @vid

      it 'uses the type of the instance in the JSON string', ->
        expect(@blData.videoType).toEqual @videoType


    describe "with a type of 'show", ->
      beforeEach ->
        @startTime = '200'
        @endTime = '300'

        @clippy.startTime = @startTime
        @clippy.endTime = @endTime

        dataString = VideoClipper.generateBLDataString 'show', @clippy
        @blData = $.parseJSON dataString

      it 'uses the vid of the instance in the JSON string', ->
        expect(@blData.videoId).toEqual @vid

      it 'uses the type of the instance in the JSON string', ->
        expect(@blData.videoType).toEqual @videoType

      it 'uses the start time of the instance in the JSON string', ->
        expect(@blData.startSeconds).toEqual @startTime

      it 'uses the end time of the instance in the JSON string', ->
        expect(@blData.endSeconds).toEqual @endTime

    describe "without an incorrect type", ->

      it "returns an empty string", ->
        expect(VideoClipper.generateBLDataString 'incorrect', @clippy).toEqual ""
  
  describe "#getCaretPosition", ->
    beforeEach -> 
      VideoClipper.cleanUp()
      loadFixtures('video_clipper_question.html')
      @testID = "button-test"
      textareaId = 'bl-text'
      @vid = '8f7wj_RcqYk'
      @videoType = 'TEST'

      @clippy = new VideoClipper
        textareaId: textareaId
        videoId: @vid
        videoType: @videoType
        buttonId: @testID

    it 'checks to see if there is a window selection', ->
      spyOn(window, 'getSelection').andReturn undefined
      @clippy.getCaretPosition()
      expect(window.getSelection).toHaveBeenCalled()

      describe 'with a window selection', ->


      describe 'without a window selection', ->
        it 'returns 0', ->
          val = @clippy.getCaretPosition()
          expect(val).toEqual 0


  describe "when stripping html", ->
    beforeEach ->
      @elementHtml = '<a rel="blModal" href="#bl-vid" class="bl">%7B%22start%22:%20%2243.92%22,%20%22end%22:%20%22330%22,%20%22type%22:%20%22show%22,%20%22modal%22:%20%22#bl-vid%22,%20%22video%22:%20%7B%22id%22:%20%228f7wj_RcqYk%22,%20%22type%22:%20%22YT%22%7D%7D</a>'

    it "creates a div", ->
      spyOn(document, "createElement").andCallThrough()
      VideoClipper.stripHTML(@elementHtml)
      expect(document.createElement).toHaveBeenCalledWith("DIV")

  describe ".secondsToTime", ->
    describe "with 0 seconds, minutes and hours of time", ->
      it "returns 0.00", ->
        expect(VideoClipper.secondsToTime("0")).toEqual "0.00"

      it 'returns an empty string if given an empty string', ->
        expect(VideoClipper.secondsToTime("")).toEqual ""

    describe "with 0 minutes and hours of time", ->
      it 'goes to two decimal places', ->
        expect(VideoClipper.secondsToTime("12.123456789")).toEqual "12.12"

    describe "with 0 hours of time", ->
      it 'goes to two decimal places', ->
        expect(VideoClipper.secondsToTime("602.123456789")).toEqual "10:02.12"

      it 'returns minutes of magnitude 10^0 formatted as M:SS.XX', ->
        expect(VideoClipper.secondsToTime("60")).toEqual "1:00.00"
        expect(VideoClipper.secondsToTime("72.1234567")).toEqual "1:12.12"
        expect(VideoClipper.secondsToTime("300.1234567")).toEqual "5:00.12"
        expect(VideoClipper.secondsToTime("599.994")).toEqual "9:59.99"

      it 'returns minutes of magnitude 10^1 formatted as MM:SS.XX', ->
        expect(VideoClipper.secondsToTime("600")).toEqual "10:00.00"
        expect(VideoClipper.secondsToTime("721.1234567")).toEqual "12:01.12"
        expect(VideoClipper.secondsToTime("1842.1234567")).toEqual "30:42.12"
        expect(VideoClipper.secondsToTime("3599.994")).toEqual "59:59.99"        


    describe "with hours, minutes and seconds of time", ->
      it 'goes to two decimal places', ->
        expect(VideoClipper.secondsToTime("3612.123456789")).toEqual "1:00:12.12"

      it 'returns hours of magnitude 10^0 formatted as H:MM:SS.XX', ->
        expect(VideoClipper.secondsToTime("3600")).toEqual "1:00:00.00"
        expect(VideoClipper.secondsToTime("7207")).toEqual "2:00:07.00"
        expect(VideoClipper.secondsToTime("10812")).toEqual "3:00:12.00"
        expect(VideoClipper.secondsToTime("14521")).toEqual "4:02:01.00"
        expect(VideoClipper.secondsToTime("18780.123")).toEqual "5:13:00.12"
        expect(VideoClipper.secondsToTime("35999.994")).toEqual "9:59:59.99"


      it 'returns hours of magnitude 10^1 formatted as HH:MM:SS.XX', ->
        expect(VideoClipper.secondsToTime("36000")).toEqual "10:00:00.00"
        expect(VideoClipper.secondsToTime("330207")).toEqual "91:43:27.00"
        expect(VideoClipper.secondsToTime("298812")).toEqual "83:00:12.00"
        expect(VideoClipper.secondsToTime("266521")).toEqual "74:02:01.00"
        expect(VideoClipper.secondsToTime("234780.123")).toEqual "65:13:00.12"
        expect(VideoClipper.secondsToTime("359999.994")).toEqual "99:59:59.99"

  describe ".timeToSeconds", ->
    describe "with 0 seconds, minutes and hours of time", ->
      it 'returns 0.00', ->
        expect(VideoClipper.timeToSeconds("0.00")).toEqual '0.00'

    describe "with 0 minutes and hours of time", ->
      it 'returns the right number of seconds', ->
        expect(VideoClipper.timeToSeconds("1.00")).toEqual '1.00'
        expect(VideoClipper.timeToSeconds("01.00")).toEqual '1.00'
        expect(VideoClipper.timeToSeconds("02.12")).toEqual '2.12'
        expect(VideoClipper.timeToSeconds("26.214")).toEqual '26.21'
        expect(VideoClipper.timeToSeconds("59.9949")).toEqual '59.99' 
      

    describe "with 0 hours of time", ->
      it 'returns the right number of seconds', ->
        expect(VideoClipper.timeToSeconds("1:00.00")).toEqual "60.00"
        expect(VideoClipper.timeToSeconds("1:12.12")).toEqual "72.12"
        expect(VideoClipper.timeToSeconds("5:00.12")).toEqual "300.12"
        expect(VideoClipper.timeToSeconds("9:59.99")).toEqual "599.99"
        expect(VideoClipper.timeToSeconds("10:00.00")).toEqual "600.00"
        expect(VideoClipper.timeToSeconds("12:01.12")).toEqual "721.12"
        expect(VideoClipper.timeToSeconds("30:42.12")).toEqual "1842.12"
        expect(VideoClipper.timeToSeconds("59:59.99")).toEqual "3599.99"  
             

    describe "with hours, minutes and seconds of time", ->
        expect(VideoClipper.timeToSeconds("1:00:00.00")).toEqual "3600.00"
        expect(VideoClipper.timeToSeconds("2:00:07.00")).toEqual "7207.00"
        expect(VideoClipper.timeToSeconds("3:00:12.00")).toEqual "10812.00"
        expect(VideoClipper.timeToSeconds("4:02:01.00")).toEqual "14521.00"
        expect(VideoClipper.timeToSeconds("5:13:00.12")).toEqual "18780.12"
        expect(VideoClipper.timeToSeconds("9:59:59.99")).toEqual "35999.99"
        expect(VideoClipper.timeToSeconds("10:00:00.00")).toEqual "36000.00"
        expect(VideoClipper.timeToSeconds("91:43:27.00")).toEqual "330207.00"
        expect(VideoClipper.timeToSeconds("83:00:12.00")).toEqual "298812.00"
        expect(VideoClipper.timeToSeconds("74:02:01.00")).toEqual "266521.00"
        expect(VideoClipper.timeToSeconds("65:13:00.12")).toEqual "234780.12"
        expect(VideoClipper.timeToSeconds("99:59:59.99")).toEqual "359999.99"


  describe ".getEndTime", ->
    beforeEach ->
      VideoClipper.cleanUp()
      loadFixtures('video_clipper_question.html')
      textareaId = 'bl-text'

      @clippy = new VideoClipper
        textareaId: textareaId
        videoId: '8f7wj_RcqYk'
        videoType: 'TEST'

    it "gets the value of input[name='bl-end']", ->
      valSpy = spyOn($.fn,'val').andCallThrough()
      VideoClipper.getEndTime()
      expect($.fn.val).toHaveBeenCalled()
      expect(valSpy.mostRecentCall.object.selector).toBe "input[name='bl-end']"

    it "passes the value through .timeToSeconds", ->
      some_val = "SOME VALUE"
      $("input[name='bl-end']").val some_val
      spyOn(VideoClipper, 'timeToSeconds')
      VideoClipper.getEndTime()
      expect(VideoClipper.timeToSeconds).toHaveBeenCalledWith some_val


  describe ".getStartTime", ->
    beforeEach ->
      VideoClipper.cleanUp()
      loadFixtures('video_clipper_question.html')
      textareaId = 'bl-text'

      @clippy = new VideoClipper
        textareaId: textareaId
        videoId: '8f7wj_RcqYk'
        videoType: 'TEST'

    it "gets the value of input[name='bl-start']", ->
      valSpy = spyOn($.fn,'val').andCallThrough()
      VideoClipper.getStartTime()
      expect($.fn.val).toHaveBeenCalled()
      expect(valSpy.mostRecentCall.object.selector).toBe "input[name='bl-start']"

    it "passes the value through .timeToSeconds", ->
      some_val = "SOME VALUE"
      $("input[name='bl-start']").val some_val
      spyOn(VideoClipper, 'timeToSeconds')
      VideoClipper.getStartTime()
      expect(VideoClipper.timeToSeconds).toHaveBeenCalledWith some_val

  describe ".setEndTime", ->
    beforeEach ->
      VideoClipper.cleanUp()
      loadFixtures('video_clipper_question.html')
      textareaId = 'bl-text'

      @clippy = new VideoClipper
        textareaId: textareaId
        videoId: '8f7wj_RcqYk'
        videoType: 'TEST'

    it 'calls .secondsToTime with the parameter val', ->
      val = "SOME VALUE"
      spyOn(VideoClipper, 'secondsToTime')
      VideoClipper.setEndTime(val)
      expect(VideoClipper.secondsToTime).toHaveBeenCalledWith val

    it "sets the 'input[name='bl-end'] box with the time value", ->
      val = 'SOME VALUE'
      val2 = 'SOME VALUE ROUND 2'
      spyOn(VideoClipper, 'secondsToTime').andReturn val2
      valSpy = spyOn($.fn, 'val').andCallThrough()
      VideoClipper.setEndTime val
      expect($.fn.val).toHaveBeenCalledWith val2
      expect(valSpy.mostRecentCall.object.selector).
        toEqual "input[name='bl-end']"

    it 'returns the value from secondsToTime', ->
      val = 'SOME VALUE'
      val2 = 'SOME VALUE ROUND 2'
      spyOn(VideoClipper, 'secondsToTime').andReturn val2
      expect(VideoClipper.setEndTime(val)).toEqual val2



  describe ".setStartTime", ->
    beforeEach ->
      VideoClipper.cleanUp()
      loadFixtures('video_clipper_question.html')
      textareaId = 'bl-text'

      @clippy = new VideoClipper
        textareaId: textareaId
        videoId: '8f7wj_RcqYk'
        videoType: 'TEST'

    it 'calls .secondsToTime with the parameter val', ->
      val = "SOME VALUE"
      spyOn(VideoClipper, 'secondsToTime')
      VideoClipper.setStartTime(val)
      expect(VideoClipper.secondsToTime).toHaveBeenCalledWith val

    it "sets the 'input[name='bl-start'] box with the time value", ->
      val = 'SOME VALUE'
      val2 = 'SOME VALUE ROUND 2'
      spyOn(VideoClipper, 'secondsToTime').andReturn val2
      valSpy = spyOn($.fn, 'val').andCallThrough()
      VideoClipper.setStartTime val
      expect($.fn.val).toHaveBeenCalledWith val2
      expect(valSpy.mostRecentCall.object.selector).
        toEqual "input[name='bl-start']"

    it 'returns the value from secondsToTime', ->
      val = 'SOME VALUE'
      val2 = 'SOME VALUE ROUND 2'
      spyOn(VideoClipper, 'secondsToTime').andReturn val2
      expect(VideoClipper.setStartTime(val)).toEqual val2


