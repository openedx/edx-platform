describe 'Tab', ->
  beforeEach ->
    loadFixtures 'coffee/fixtures/tab.html'
    @items = $.parseJSON readFixtures('coffee/fixtures/items.json')

  describe 'constructor', ->
    beforeEach ->
      spyOn($.fn, 'tabs')
      @tab = new Tab 1, @items

    it 'set the element', ->
      expect(@tab.el).toEqual $('#tab_1')

    it 'build the tabs', ->
      links = $('.navigation li>a').map(-> $(this).attr('href')).get()
      expect(links).toEqual ['#tab-1-0', '#tab-1-1', '#tab-1-2']

    it 'build the container', ->
      containers = $('section').map(-> $(this).attr('id')).get()
      expect(containers).toEqual ['tab-1-0', 'tab-1-1', 'tab-1-2']

    it 'bind the tabs', ->
      expect($.fn.tabs).toHaveBeenCalledWith show: @tab.onShow

  # As of jQuery 1.9, the onShow callback is deprecated
  # http://jqueryui.com/upgrade-guide/1.9/#deprecated-show-event-renamed-to-activate
  # The code below tests that onShow does what is expected,
  # but note that onShow will NOT be called when the user
  # clicks on the tab if we're using jQuery version >= 1.9
  describe 'onShow', ->
    beforeEach ->
      @tab = new Tab 1, @items
      @tab.onShow($('#tab-1-0'), {'index': 1})

    it 'replace content in the container', ->
      @tab.onShow($('#tab-1-1'), {'index': 1})
      expect($('#tab-1-0').html()).toEqual ''
      expect($('#tab-1-1').html()).toEqual 'Video 2'
      expect($('#tab-1-2').html()).toEqual ''

    it 'trigger contentChanged event on the element', ->
      spyOnEvent @tab.el, 'contentChanged'
      @tab.onShow($('#tab-1-1'), {'index': 1})
      expect('contentChanged').toHaveBeenTriggeredOn @tab.el
