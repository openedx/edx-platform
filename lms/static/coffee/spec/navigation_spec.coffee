describe 'Navigation', ->
  beforeEach ->
    loadFixtures 'coffee/fixtures/accordion.html'
    @navigation = new Navigation

  describe 'constructor', ->
    describe 'when the #accordion exists', ->
      describe 'when there is an active section', ->
        beforeEach ->
          spyOn $.fn, 'accordion'
          $('#accordion').append('<ul><li></li></ul><ul><li class="active"></li></ul>')
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
          $('#accordion').append('<ul><li></li></ul><ul><li></li></ul>')
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
