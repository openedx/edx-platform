(function() {

  describe('Tab', function() {
    beforeEach(function() {
      loadFixtures('tab.html');
      return this.items = $.parseJSON(readFixtures('items.json'));
    });
    describe('constructor', function() {
      beforeEach(function() {
        spyOn($.fn, 'tabs');
        return this.tab = new Tab(1, this.items);
      });
      it('set the element', function() {
        return expect(this.tab.element).toEqual($('#tab_1'));
      });
      it('build the tabs', function() {
        var links;
        links = $('.navigation li>a').map(function() {
          return $(this).attr('href');
        }).get();
        return expect(links).toEqual(['#tab-1-0', '#tab-1-1', '#tab-1-2']);
      });
      it('build the container', function() {
        var containers;
        containers = $('section').map(function() {
          return $(this).attr('id');
        }).get();
        return expect(containers).toEqual(['tab-1-0', 'tab-1-1', 'tab-1-2']);
      });
      return it('bind the tabs', function() {
        return expect($.fn.tabs).toHaveBeenCalledWith({
          show: this.tab.onShow
        });
      });
    });
    return describe('onShow', function() {
      beforeEach(function() {
        this.tab = new Tab(1, this.items);
        return $('[href="#tab-1-0"]').click();
      });
      it('replace content in the container', function() {
        $('[href="#tab-1-1"]').click();
        expect($('#tab-1-0').html()).toEqual('');
        expect($('#tab-1-1').html()).toEqual('Video 2');
        return expect($('#tab-1-2').html()).toEqual('');
      });
      return it('trigger contentChanged event on the element', function() {
        spyOnEvent(this.tab.element, 'contentChanged');
        $('[href="#tab-1-1"]').click();
        return expect('contentChanged').toHaveBeenTriggeredOn(this.tab.element);
      });
    });
  });

}).call(this);
