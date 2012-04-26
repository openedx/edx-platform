describe 'Courseware', ->
  describe 'bind', ->
    it 'bind the navigation', ->
      spyOn Courseware.Navigation, 'bind'
      Courseware.bind()
      expect(Courseware.Navigation.bind).toHaveBeenCalled()

  describe 'Navigation', ->
    beforeEach ->
      loadFixtures 'accordion.html'
      @navigation = new Courseware.Navigation

    describe 'bind', ->
      describe 'when the #accordion exists', ->
        it 'activate the accordion with correct active section', ->
          spyOn $.fn, 'accordion'
          $('#accordion').append('<ul><li></li></ul><ul><li class="active"></li></ul>')
          Courseware.Navigation.bind()
          expect($('#accordion').accordion).toHaveBeenCalledWith
            active: 1
            header: 'h3'
            autoHeight: false

        it 'binds the accordionchange event', ->
          Courseware.Navigation.bind()
          expect($('#accordion')).toHandleWith 'accordionchange', @navigation.log

        it 'bind the navigation toggle', ->
          Courseware.Navigation.bind()
          expect($('#open_close_accordion a')).toHandleWith 'click', @navigation.toggle

      describe 'when the #accordion does not exists', ->
        beforeEach ->
          $('#accordion').remove()

        it 'does not activate the accordion', ->
          spyOn $.fn, 'accordion'
          Courseware.Navigation.bind()
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
        window.log_event = ->
        spyOn window, 'log_event'

      it 'submit event log', ->
        @navigation.log {}, {
          newHeader:
            text: -> "new"
          oldHeader:
            text: -> "old"
        }

        expect(window.log_event).toHaveBeenCalledWith 'accordion',
          newheader: 'new'
          oldheader: 'old'
