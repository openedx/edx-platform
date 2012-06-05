describe 'VideoCaption', ->
  beforeEach ->
    @player = jasmine.stubVideoPlayer @

  afterEach ->
    YT.Player = undefined
    $.fn.scrollTo.reset()

  describe 'constructor', ->
    beforeEach ->
      spyOn($, 'getWithPrefix').andCallThrough()

    describe 'always', ->
      beforeEach ->
        @caption = new VideoCaption @player, 'def456'

      it 'set the player', ->
        expect(@caption.player).toEqual @player

      it 'set the youtube id', ->
        expect(@caption.youtubeId).toEqual 'def456'

      it 'create the caption element', ->
        expect($('.video')).toContain 'ol.subtitles'

      it 'add caption control to video player', ->
        expect($('.video')).toContain 'a.hide-subtitles'

      it 'fetch the caption', ->
        expect($.getWithPrefix).toHaveBeenCalledWith @caption.captionURL(), jasmine.any(Function)

      it 'bind window resize event', ->
        expect($(window)).toHandleWith 'resize', @caption.onWindowResize

      it 'bind player resize event', ->
        expect($(@player)).toHandleWith 'resize', @caption.onWindowResize

      it 'bind player updatePlayTime event', ->
        expect($(@player)).toHandleWith 'updatePlayTime', @caption.onUpdatePlayTime

      it 'bind player play event', ->
        expect($(@player)).toHandleWith 'play', @caption.onPlay

      it 'bind the hide caption button', ->
        expect($('.hide-subtitles')).toHandleWith 'click', @caption.toggle

      it 'bind the mouse movement', ->
        expect($('.subtitles')).toHandleWith 'mouseenter', @caption.onMouseEnter
        expect($('.subtitles')).toHandleWith 'mouseleave', @caption.onMouseLeave
        expect($('.subtitles')).toHandleWith 'mousemove', @caption.onMovement
        expect($('.subtitles')).toHandleWith 'mousewheel', @caption.onMovement
        expect($('.subtitles')).toHandleWith 'DOMMouseScroll', @caption.onMovement

    describe 'when on a non touch-based device', ->
      beforeEach ->
        spyOn(window, 'onTouchBasedDevice').andReturn false
        @caption = new VideoCaption @player, 'def456'

      it 'render the caption', ->
        expect($('.subtitles').html()).toMatch new RegExp('''
          <li data-index="0" data-start="0">Caption at 0</li>
          <li data-index="1" data-start="10000">Caption at 10000</li>
          <li data-index="2" data-start="20000">Caption at 20000</li>
          <li data-index="3" data-start="30000">Caption at 30000</li>
        '''.replace(/\n/g, ''))

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
        spyOn(window, 'onTouchBasedDevice').andReturn true
        @caption = new VideoCaption @player, 'def456'

      it 'show explaination message', ->
        expect($('.subtitles li')).toHaveHtml "Caption will be displayed when you start playing the video."

      it 'does not set rendered to true', ->
        expect(@caption.rendered).toBeFalsy()

  describe 'mouse movement', ->
    beforeEach ->
      spyOn(window, 'setTimeout').andReturn 100
      spyOn window, 'clearTimeout'
      @caption = new VideoCaption @player, 'def456'

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
          spyOn(@player, 'isPlaying').andReturn true
          $('.subtitles li[data-index]:first').addClass 'current'
          $('.subtitles').trigger jQuery.Event 'mouseout'

        it 'scroll the caption', ->
          expect($.fn.scrollTo).toHaveBeenCalled()

      describe 'when the player is not playing', ->
        beforeEach ->
          spyOn(@player, 'isPlaying').andReturn false
          $('.subtitles').trigger jQuery.Event 'mouseout'

        it 'does not scroll the caption', ->
          expect($.fn.scrollTo).not.toHaveBeenCalled()

  describe 'search', ->
    beforeEach ->
      @caption = new VideoCaption @player, 'def456'

    it 'return a correct caption index', ->
      expect(@caption.search(0)).toEqual 0
      expect(@caption.search(9999)).toEqual 0
      expect(@caption.search(10000)).toEqual 1
      expect(@caption.search(15000)).toEqual 1
      expect(@caption.search(30000)).toEqual 3
      expect(@caption.search(30001)).toEqual 3

  describe 'onPlay', ->
    describe 'when the caption was not rendered', ->
      beforeEach ->
        spyOn(window, 'onTouchBasedDevice').andReturn true
        @caption = new VideoCaption @player, 'def456'
        @caption.onPlay()

      it 'render the caption', ->
        expect($('.subtitles').html()).toMatch new RegExp('''
          <li data-index="0" data-start="0">Caption at 0</li>
          <li data-index="1" data-start="10000">Caption at 10000</li>
          <li data-index="2" data-start="20000">Caption at 20000</li>
          <li data-index="3" data-start="30000">Caption at 30000</li>
        '''.replace(/\n/g, ''))

      it 'add a padding element to caption', ->
        expect($('.subtitles li:first')).toBe '.spacing'
        expect($('.subtitles li:last')).toBe '.spacing'

      it 'bind all the caption link', ->
        $('.subtitles li[data-index]').each (index, link) =>
          expect($(link)).toHandleWith 'click', @caption.seekPlayer

      it 'set rendered to true', ->
        expect(@caption.rendered).toBeTruthy()

  describe 'onUpdatePlayTime', ->
    beforeEach ->
      @caption = new VideoCaption @player, 'def456'

    describe 'when the video speed is 1.0x', ->
      beforeEach ->
        @video.setSpeed '1.0'
        @caption.onUpdatePlayTime {}, 25.000

      it 'search the caption based on time', ->
        expect(@caption.currentIndex).toEqual 2

    describe 'when the video speed is not 1.0x', ->
      beforeEach ->
        @video.setSpeed '0.75'
        @caption.onUpdatePlayTime {}, 25.000

      it 'search the caption based on 1.0x speed', ->
        expect(@caption.currentIndex).toEqual 1

    describe 'when the index is not the same', ->
      beforeEach ->
        @caption.currentIndex = 1
        $('.subtitles li[data-index=1]').addClass 'current'
        @caption.onUpdatePlayTime {}, 25.000

      it 'deactivate the previous caption', ->
        expect($('.subtitles li[data-index=1]')).not.toHaveClass 'current'

      it 'activate new caption', ->
        expect($('.subtitles li[data-index=2]')).toHaveClass 'current'

      it 'save new index', ->
        expect(@caption.currentIndex).toEqual 2

      it 'scroll caption to new position', ->
        expect($.fn.scrollTo).toHaveBeenCalled()

    describe 'when the index is the same', ->
      beforeEach ->
        @caption.currentIndex = 1
        $('.subtitles li[data-index=1]').addClass 'current'
        @caption.onUpdatePlayTime {}, 15.000

      it 'does not change current subtitle', ->
        expect($('.subtitles li[data-index=1]')).toHaveClass 'current'

  describe 'onWindowResize', ->
    beforeEach ->
      @caption = new VideoCaption @player, 'def456'
      $('.subtitles li[data-index=1]').addClass 'current'
      @caption.onWindowResize()

    it 'set the height of caption container', ->
      expect(parseInt($('.subtitles').css('maxHeight'))).toEqual $('.video-wrapper').height()

    it 'set the height of caption spacing', ->
      expect(parseInt($('.subtitles .spacing:first').css('height'))).toEqual(
        $('.video-wrapper').height() / 2 - $('.subtitles li:not(.spacing):first').height() / 2)
      expect(parseInt($('.subtitles .spacing:last').css('height'))).toEqual(
        $('.video-wrapper').height() / 2 - $('.subtitles li:not(.spacing):last').height() / 2)

    it 'scroll caption to new position', ->
      expect($.fn.scrollTo).toHaveBeenCalled()

  describe 'scrollCaption', ->
    beforeEach ->
      @caption = new VideoCaption @player, 'def456'

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
          expect($.fn.scrollTo).toHaveBeenCalledWith $('.subtitles .current:first', @player.element),
            offset: - ($('.video-wrapper').height() / 2 - $('.subtitles .current:first').height() / 2)

  describe 'seekPlayer', ->
    beforeEach ->
      @caption = new VideoCaption @player, 'def456'
      @time = null
      $(@player).bind 'seek', (event, time) => @time = time

    describe 'when the video speed is 1.0x', ->
      beforeEach ->
        @video.setSpeed '1.0'
        $('.subtitles li[data-start="30000"]').click()

      it 'trigger seek event with the correct time', ->
        expect(@time).toEqual 30.000

    describe 'when the video speed is not 1.0x', ->
      beforeEach ->
        @video.setSpeed '0.75'
        $('.subtitles li[data-start="30000"]').click()

      it 'trigger seek event with the correct time', ->
        expect(@time).toEqual 40.000

  describe 'toggle', ->
    beforeEach ->
      @caption = new VideoCaption @player, 'def456'
      $('.subtitles li[data-index=1]').addClass 'current'

    describe 'when the caption is visible', ->
      beforeEach ->
        @player.element.removeClass 'closed'
        @caption.toggle jQuery.Event('click')

      it 'hide the caption', ->
        expect(@player.element).toHaveClass 'closed'


    describe 'when the caption is hidden', ->
      beforeEach ->
        @player.element.addClass 'closed'
        @caption.toggle jQuery.Event('click')

      it 'show the caption', ->
        expect(@player.element).not.toHaveClass 'closed'

      it 'scroll the caption', ->
        expect($.fn.scrollTo).toHaveBeenCalled()
