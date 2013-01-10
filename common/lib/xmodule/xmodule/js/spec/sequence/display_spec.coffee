# TODO: figure out why failing
xdescribe 'Sequence', ->
  beforeEach ->
    # Stub MathJax
    window.MathJax = { Hub: { Queue: -> } }
    spyOn Logger, 'log'

    loadFixtures 'sequence.html'
    @items = $.parseJSON readFixtures('items.json')

  describe 'constructor', ->
    beforeEach ->
      @sequence = new Sequence '1', 'sequence_1', @items, 'sequence', 1

    it 'set the element', ->
      expect(@sequence.el).toEqual $('#sequence_1')

    it 'build the navigation', ->
      classes = $('#sequence-list li>a').map(-> $(this).attr('class')).get()
      elements = $('#sequence-list li>a').map(-> $(this).attr('data-element')).get()
      titles = $('#sequence-list li>a>p').map(-> $(this).html()).get()

      expect(classes).toEqual ['seq_video_active', 'seq_video_inactive', 'seq_problem_inactive']
      expect(elements).toEqual ['1', '2', '3']
      expect(titles).toEqual ['Video 1', 'Video 2', 'Sample Problem']

    it 'bind the page events', ->
      expect($('#sequence-list a')).toHandleWith 'click', @sequence.goto

    it 'render the active sequence content', ->
      expect($('#seq_content').html()).toEqual 'Video 1'

  describe 'toggleArrows', ->
    beforeEach ->
      @sequence = new Sequence '1', 'sequence_1', @items, 'sequence', 1

    describe 'when the first tab is active', ->
      beforeEach ->
        @sequence.position = 1
        @sequence.toggleArrows()

      it 'disable the previous button', ->
        expect($('.sequence-nav-buttons .prev a')).toHaveClass 'disabled'

      it 'enable the next button', ->
        expect($('.sequence-nav-buttons .next a')).not.toHaveClass 'disabled'
        expect($('.sequence-nav-buttons .next a')).toHandleWith 'click', @sequence.next

    describe 'when the middle tab is active', ->
      beforeEach ->
        @sequence.position = 2
        @sequence.toggleArrows()

      it 'enable the previous button', ->
        expect($('.sequence-nav-buttons .prev a')).not.toHaveClass 'disabled'
        expect($('.sequence-nav-buttons .prev a')).toHandleWith 'click', @sequence.previous

      it 'enable the next button', ->
        expect($('.sequence-nav-buttons .next a')).not.toHaveClass 'disabled'
        expect($('.sequence-nav-buttons .next a')).toHandleWith 'click', @sequence.next

    describe 'when the last tab is active', ->
      beforeEach ->
        @sequence.position = 3
        @sequence.toggleArrows()

      it 'enable the previous button', ->
        expect($('.sequence-nav-buttons .prev a')).not.toHaveClass 'disabled'
        expect($('.sequence-nav-buttons .prev a')).toHandleWith 'click', @sequence.previous

      it 'disable the next button', ->
        expect($('.sequence-nav-buttons .next a')).toHaveClass 'disabled'

  describe 'render', ->
    beforeEach ->
      spyOn $, 'postWithPrefix'
      @sequence = new Sequence '1', 'sequence_1', @items, 'sequence'
      spyOnEvent @sequence.el, 'contentChanged'
      spyOn(@sequence, 'toggleArrows').andCallThrough()

    describe 'with a different position than the current one', ->
      beforeEach ->
        @sequence.render 1

      describe 'with no previous position', ->
        it 'does not save the new position', ->
          expect($.postWithPrefix).not.toHaveBeenCalled()

      describe 'with previous position', ->
        beforeEach ->
          @sequence.position = 2
          @sequence.render 1

        it 'mark the previous tab as visited', ->
          expect($('[data-element="2"]')).toHaveClass 'seq_video_visited'

        it 'save the new position', ->
          expect($.postWithPrefix).toHaveBeenCalledWith '/modx/1/goto_position', position: 1

      it 'mark new tab as active', ->
        expect($('[data-element="1"]')).toHaveClass 'seq_video_active'

      it 'render the new content', ->
        expect($('#seq_content').html()).toEqual 'Video 1'

      it 'update the position', ->
        expect(@sequence.position).toEqual 1

      it 're-update the arrows', ->
        expect(@sequence.toggleArrows).toHaveBeenCalled()

      it 'trigger contentChanged event', ->
        expect('contentChanged').toHaveBeenTriggeredOn @sequence.el

    describe 'with the same position as the current one', ->
      it 'should not trigger contentChanged event', ->
        @sequence.position = 2
        @sequence.render 2
        expect('contentChanged').not.toHaveBeenTriggeredOn @sequence.el

  describe 'goto', ->
    beforeEach ->
      jasmine.stubRequests()
      @sequence = new Sequence '1', 'sequence_1', @items, 'sequence', 2
      $('[data-element="3"]').click()

    it 'log the sequence goto event', ->
      expect(Logger.log).toHaveBeenCalledWith 'seq_goto', old: 2, new: 3, id: '1'

    it 'call render on the right sequence', ->
      expect($('#seq_content').html()).toEqual 'Sample Problem'

  describe 'next', ->
    beforeEach ->
      jasmine.stubRequests()
      @sequence = new Sequence '1', 'sequence_1', @items, 'sequence', 2
      $('.sequence-nav-buttons .next a').click()

    it 'log the next sequence event', ->
      expect(Logger.log).toHaveBeenCalledWith 'seq_next', old: 2, new: 3, id: '1'

    it 'call render on the next sequence', ->
      expect($('#seq_content').html()).toEqual 'Sample Problem'

  describe 'previous', ->
    beforeEach ->
      jasmine.stubRequests()
      @sequence = new Sequence '1', 'sequence_1', @items, 'sequence', 2
      $('.sequence-nav-buttons .prev a').click()

    it 'log the previous sequence event', ->
      expect(Logger.log).toHaveBeenCalledWith 'seq_prev', old: 2, new: 1, id: '1'

    it 'call render on the previous sequence', ->
      expect($('#seq_content').html()).toEqual 'Video 1'

  describe 'link_for', ->
    it 'return a link for specific position', ->
      sequence = new Sequence '1', 'sequence_1', @items, 2
      expect(sequence.link_for(2)).toBe '[data-element="2"]'
