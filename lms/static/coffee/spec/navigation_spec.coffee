describe 'Navigation', ->
  beforeEach ->
    loadFixtures 'coffee/fixtures/accordion.html'
    @navigation = new Navigation

  describe 'constructor', ->
    describe 'when the #accordion exists', ->
      describe 'when there is an active section', ->
        beforeEach ->
          spyOn $.fn, 'accordion'
          $('#accordion').append('<div><div><ol><li></li></ol></div></div><div><div><ol><li class="active"></li></ol></div></div>')
          new Navigation

        it 'activate the accordion with correct active section', ->
          expect($('#accordion').accordion).toHaveBeenCalledWith
            active: 1
            header: 'h3'
            autoHeight: false
            heightStyle: 'content'

      describe 'when there is no active section', ->
        beforeEach ->
          spyOn $.fn, 'accordion'
          $('#accordion').append('<div><div><ol><li></li></ol></div></div><div><div><ol><li></li></ol></div></div>')
          new Navigation

        it 'activate the accordian with no section as active', ->
          expect($('#accordion').accordion).toHaveBeenCalledWith
            active: 0
            header: 'h3'
            autoHeight: false
            heightStyle: 'content'

      it 'binds the accordionchange event', ->
        expect($('#accordion')).toHandleWith 'accordionchange', @navigation.log

      it 'bind the navigation toggle', ->
        expect($('#open_close_accordion a')).toHandleWith 'click', @navigation.toggle

      it 'bind the setChapter', ->
        expect($('#accordion .chapter')).toHandleWith 'click', @navigation.setChapter

    describe 'when the #accordion does not exists', ->
      beforeEach ->
        $('#accordion').remove()

      it 'does not activate the accordion', ->
        spyOn $.fn, 'accordion'
        expect($('#accordion').accordion).wasNotCalled()

  describe 'toggle', ->
    it 'toggle closed class on the wrapper', ->
      $('.course-wrapper').removeClass('closed')

      @navigation.toggle()
      expect($('.course-wrapper')).toHaveClass('closed')

      @navigation.toggle()
      expect($('.course-wrapper')).not.toHaveClass('closed')

  describe 'log', ->
    beforeEach ->
      spyOn Logger, 'log'

    it 'submit event log', ->
      @navigation.log {}, {
        newHeader:
          text: -> "new"
        oldHeader:
          text: -> "old"
      }

      expect(Logger.log).toHaveBeenCalledWith 'accordion',
        newheader: 'new'
        oldheader: 'old'

  describe 'setChapter', ->
    beforeEach ->
      $('#accordion').append('<div><div><ol><li class="active"><a href="#"></a></li></ol></div></div>')
      new Navigation
    it 'Chapter opened', ->
      e = jQuery.Event('click')
      $('#accordion .chapter').trigger(e)
      expect($('.chapter')).toHaveClass('is-open')

    it 'content active on chapter opened', ->
      e = jQuery.Event('click')
      $('#accordion .chapter').trigger(e)
      expect($('.chapter').next('div').children('div')).toHaveClass('ui-accordion-content-active')
      expect($('.ui-accordion-content-active')).toHaveAttr('aria-hidden', 'false')

    it 'focus move to first child on chapter opened', ->
      spyOn($.fn, 'focus')
      e = jQuery.Event('click')
      $('#accordion .chapter').trigger(e)
      expect($('.ui-accordion-content-active li:first-child a').focus).toHaveBeenCalled()

