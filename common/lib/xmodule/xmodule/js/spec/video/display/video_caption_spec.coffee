describe 'VideoCaption', ->

  beforeEach ->
    spyOn(VideoCaption.prototype, 'fetchCaption').andCallThrough()
    spyOn($, 'ajaxWithPrefix').andCallThrough()
    window.onTouchBasedDevice = jasmine.createSpy('onTouchBasedDevice').andReturn false

  afterEach ->
    YT.Player = undefined
    $.fn.scrollTo.reset()
    $('.subtitles').remove()

  describe 'constructor', ->

    describe 'always', ->

      beforeEach ->
        @player = jasmine.stubVideoPlayer @
        @caption = @player.caption

      it 'set the youtube id', ->
        expect(@caption.youtubeId).toEqual 'normalSpeedYoutubeId'

      it 'create the caption element', ->
        expect($('.video')).toContain 'ol.subtitles'

      it 'add caption control to video player', ->
        expect($('.video')).toContain 'a.hide-subtitles'

      it 'fetch the caption', ->
        expect(@caption.loaded).toBeTruthy()
        expect(@caption.fetchCaption).toHaveBeenCalled()
        expect($.ajaxWithPrefix).toHaveBeenCalledWith
          url: @caption.captionURL()
          notifyOnError: false
          success: jasmine.any(Function)

      it 'bind window resize event', ->
        expect($(window)).toHandleWith 'resize', @caption.resize

      it 'bind the hide caption button', ->
        expect($('.hide-subtitles')).toHandleWith 'click', @caption.toggle

      it 'bind the mouse movement', ->
        expect($('.subtitles')).toHandleWith 'mouseover', @caption.onMouseEnter
        expect($('.subtitles')).toHandleWith 'mouseout', @caption.onMouseLeave
        expect($('.subtitles')).toHandleWith 'mousemove', @caption.onMovement
        expect($('.subtitles')).toHandleWith 'mousewheel', @caption.onMovement
        expect($('.subtitles')).toHandleWith 'DOMMouseScroll', @caption.onMovement

    describe 'when on a non touch-based device', ->

      beforeEach ->
        @player = jasmine.stubVideoPlayer @
        @caption = @player.caption

      it 'render the caption', ->
        captionsData = jasmine.stubbedCaption
        $('.subtitles li[data-index]').each (index, link) =>
          expect($(link)).toHaveData 'index', index
          expect($(link)).toHaveData 'start', captionsData.start[index]
          expect($(link)).toHaveText captionsData.text[index]

      it 'add a padding element to caption', ->
        expect($('.subtitles li:first')).toBe '.spacing'
        expect($('.subtitles li:last')).toBe '.spacing'

      it 'bind all the caption link', ->
        $('.subtitles li[data-index]').each (index, link) =>
          expect($(link)).toHandleWith 'click', @caption.seekPlayer

      it 'set rendered to true', ->
        expect(@caption.rendered).toBeTruthy()

    describe 'when on a touch-based device', ->

      beforeEach ->
        window.onTouchBasedDevice.andReturn true
        @player = jasmine.stubVideoPlayer @
        @caption = @player.caption

      it 'show explaination message', ->
        expect($('.subtitles li')).toHaveHtml "Caption will be displayed when you start playing the video."

      it 'does not set rendered to true', ->
        expect(@caption.rendered).toBeFalsy()

  describe 'mouse movement', ->

    beforeEach ->
      @player = jasmine.stubVideoPlayer @
      @caption = @player.caption
      window.setTimeout.andReturn(100)
      spyOn window, 'clearTimeout'

    describe 'when cursor is outside of the caption box', ->

      beforeEach ->
        $(window).trigger jQuery.Event 'mousemove'

      it 'does not set freezing timeout', ->
        expect(@caption.frozen).toBeFalsy()

    describe 'when cursor is in the caption box', ->

      beforeEach ->
        $('.subtitles').trigger jQuery.Event 'mouseenter'

      it 'set the freezing timeout', ->
        expect(@caption.frozen).toEqual 100

      describe 'when the cursor is moving', ->
        beforeEach ->
          $('.subtitles').trigger jQuery.Event 'mousemove'

        it 'reset the freezing timeout', ->
          expect(window.clearTimeout).toHaveBeenCalledWith 100

      describe 'when the mouse is scrolling', ->
        beforeEach ->
          $('.subtitles').trigger jQuery.Event 'mousewheel'

        it 'reset the freezing timeout', ->
          expect(window.clearTimeout).toHaveBeenCalledWith 100

    describe 'when cursor is moving out of the caption box', ->
      beforeEach ->
        @caption.frozen = 100
        $.fn.scrollTo.reset()

      describe 'always', ->
        beforeEach ->
          $('.subtitles').trigger jQuery.Event 'mouseout'

        it 'reset the freezing timeout', ->
          expect(window.clearTimeout).toHaveBeenCalledWith 100

        it 'unfreeze the caption', ->
          expect(@caption.frozen).toBeNull()

      describe 'when the player is playing', ->
        beforeEach ->
          @caption.playing = true
          $('.subtitles li[data-index]:first').addClass 'current'
          $('.subtitles').trigger jQuery.Event 'mouseout'

        it 'scroll the caption', ->
          expect($.fn.scrollTo).toHaveBeenCalled()

      describe 'when the player is not playing', ->
        beforeEach ->
          @caption.playing = false
          $('.subtitles').trigger jQuery.Event 'mouseout'

        it 'does not scroll the caption', ->
          expect($.fn.scrollTo).not.toHaveBeenCalled()

  describe 'search', ->

    beforeEach ->
      @player = jasmine.stubVideoPlayer @
      @caption = @player.caption

    it 'return a correct caption index', ->
      expect(@caption.search(0)).toEqual 0
      expect(@caption.search(9999)).toEqual 2
      expect(@caption.search(10000)).toEqual 2
      expect(@caption.search(15000)).toEqual 3
      expect(@caption.search(30000)).toEqual 7
      expect(@caption.search(30001)).toEqual 7

  describe 'play', ->
    describe 'when the caption was not rendered', ->
      beforeEach ->
        window.onTouchBasedDevice.andReturn true
        @player = jasmine.stubVideoPlayer @
        @caption = @player.caption
        @caption.play()

      it 'render the caption', ->
        captionsData = jasmine.stubbedCaption
        $('.subtitles li[data-index]').each (index, link) =>
          expect($(link)).toHaveData 'index', index
          expect($(link)).toHaveData 'start', captionsData.start[index]
          expect($(link)).toHaveText captionsData.text[index]

      it 'add a padding element to caption', ->
        expect($('.subtitles li:first')).toBe '.spacing'
        expect($('.subtitles li:last')).toBe '.spacing'

      it 'bind all the caption link', ->
        $('.subtitles li[data-index]').each (index, link) =>
          expect($(link)).toHandleWith 'click', @caption.seekPlayer

      it 'set rendered to true', ->
        expect(@caption.rendered).toBeTruthy()

      it 'set playing to true', ->
        expect(@caption.playing).toBeTruthy()

  describe 'pause', ->
    beforeEach ->
      @player = jasmine.stubVideoPlayer @
      @caption = @player.caption
      @caption.playing = true
      @caption.pause()

    it 'set playing to false', ->
      expect(@caption.playing).toBeFalsy()

  describe 'updatePlayTime', ->

    beforeEach ->
      @player = jasmine.stubVideoPlayer @
      @caption = @player.caption

    describe 'when the video speed is 1.0x', ->
      beforeEach ->
        @caption.currentSpeed = '1.0'
        @caption.updatePlayTime 25.000

      it 'search the caption based on time', ->
        expect(@caption.currentIndex).toEqual 5

    describe 'when the video speed is not 1.0x', ->
      beforeEach ->
        @caption.currentSpeed = '0.75'
        @caption.updatePlayTime 25.000

      it 'search the caption based on 1.0x speed', ->
        expect(@caption.currentIndex).toEqual 3

    describe 'when the index is not the same', ->
      beforeEach ->
        @caption.currentIndex = 1
        $('.subtitles li[data-index=1]').addClass 'current'
        @caption.updatePlayTime 25.000

      it 'deactivate the previous caption', ->
        expect($('.subtitles li[data-index=1]')).not.toHaveClass 'current'

      it 'activate new caption', ->
        expect($('.subtitles li[data-index=5]')).toHaveClass 'current'

      it 'save new index', ->
        expect(@caption.currentIndex).toEqual 5

      it 'scroll caption to new position', ->
        expect($.fn.scrollTo).toHaveBeenCalled()

    describe 'when the index is the same', ->
      beforeEach ->
        @caption.currentIndex = 1
        $('.subtitles li[data-index=3]').addClass 'current'
        @caption.updatePlayTime 15.000

      it 'does not change current subtitle', ->
        expect($('.subtitles li[data-index=3]')).toHaveClass 'current'

  describe 'resize', ->

    beforeEach ->
      @player = jasmine.stubVideoPlayer @
      @caption = @player.caption
      $('.subtitles li[data-index=1]').addClass 'current'
      @caption.resize()

    it 'set the height of caption container', ->
      expect(parseInt($('.subtitles').css('maxHeight'))).toBeCloseTo $('.video-wrapper').height(), 2

    it 'set the height of caption spacing', ->
      expect(Math.abs(parseInt($('.subtitles .spacing:first').css('height')) - @caption.topSpacingHeight())).toBeLessThan 1
      expect(Math.abs(parseInt($('.subtitles .spacing:last').css('height')) - @caption.bottomSpacingHeight())).toBeLessThan 1


    it 'scroll caption to new position', ->
      expect($.fn.scrollTo).toHaveBeenCalled()

  describe 'scrollCaption', ->

    beforeEach ->
      @player = jasmine.stubVideoPlayer @
      @caption = @player.caption

    describe 'when frozen', ->
      beforeEach ->
        @caption.frozen = true
        $('.subtitles li[data-index=1]').addClass 'current'
        @caption.scrollCaption()

      it 'does not scroll the caption', ->
        expect($.fn.scrollTo).not.toHaveBeenCalled()

    describe 'when not frozen', ->
      beforeEach ->
        @caption.frozen = false

      describe 'when there is no current caption', ->
        beforeEach ->
          @caption.scrollCaption()

        it 'does not scroll the caption', ->
          expect($.fn.scrollTo).not.toHaveBeenCalled()

      describe 'when there is a current caption', ->
        beforeEach ->
          $('.subtitles li[data-index=1]').addClass 'current'
          @caption.scrollCaption()

        it 'scroll to current caption', ->
          expect($.fn.scrollTo).toHaveBeenCalledWith $('.subtitles .current:first', @caption.el),
            offset: - ($('.video-wrapper').height() / 2 - $('.subtitles .current:first').height() / 2)

  describe 'seekPlayer', ->

    beforeEach ->
      @player = jasmine.stubVideoPlayer @
      @caption = @player.caption
      @time = null
      $(@caption).bind 'seek', (event, time) => @time = time

    describe 'when the video speed is 1.0x', ->
      beforeEach ->
        @caption.currentSpeed = '1.0'
        $('.subtitles li[data-start="27900"]').trigger('click')

      it 'trigger seek event with the correct time', ->
        expect(@time).toEqual 28.000

    describe 'when the video speed is not 1.0x', ->
      beforeEach ->
        @caption.currentSpeed = '0.75'
        $('.subtitles li[data-start="27900"]').trigger('click')

      it 'trigger seek event with the correct time', ->
        expect(@time).toEqual 37.000

  describe 'toggle', ->
    beforeEach ->
      @player = jasmine.stubVideoPlayer @
      @caption = @player.caption
      $('.subtitles li[data-index=1]').addClass 'current'

    describe 'when the caption is visible', ->
      beforeEach ->
        @caption.el.removeClass 'closed'
        @caption.toggle jQuery.Event('click')

      it 'hide the caption', ->
        expect(@caption.el).toHaveClass 'closed'

    describe 'when the caption is hidden', ->
      beforeEach ->
        @caption.el.addClass 'closed'
        @caption.toggle jQuery.Event('click')

      it 'show the caption', ->
        expect(@caption.el).not.toHaveClass 'closed'

      it 'scroll the caption', ->
        expect($.fn.scrollTo).toHaveBeenCalled()
