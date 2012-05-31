describe 'Tab', ->
  beforeEach ->
    loadFixtures 'tab.html'
    @items = $.parseJSON readFixtures('items.json')

  describe 'constructor', ->
    beforeEach ->
      spyOn($.fn, 'tabs')
      @tab = new Tab 1, @items

    it 'set the element', ->
      expect(@tab.element).toEqual $('#tab_1')

    it 'build the tabs', ->
      links = $('.navigation li>a').map(-> $(this).attr('href')).get()
      expect(links).toEqual ['#tab-1-0', '#tab-1-1', '#tab-1-2']

    it 'build the container', ->
      containers = $('section').map(-> $(this).attr('id')).get()
      expect(containers).toEqual ['tab-1-0', 'tab-1-1', 'tab-1-2']

    it 'bind the tabs', ->
      expect($.fn.tabs).toHaveBeenCalledWith show: @tab.onShow

  describe 'onShow', ->
    beforeEach ->
      @tab = new Tab 1, @items
      $('[href="#tab-1-0"]').click()

    it 'replace content in the container', ->
      $('[href="#tab-1-1"]').click()
      expect($('#tab-1-0').html()).toEqual ''
      expect($('#tab-1-1').html()).toEqual 'Video 2'
      expect($('#tab-1-2').html()).toEqual ''

    it 'trigger contentChanged event on the element', ->
      spyOnEvent @tab.element, 'contentChanged'
      $('[href="#tab-1-1"]').click()
      expect('contentChanged').toHaveBeenTriggeredOn @tab.element
