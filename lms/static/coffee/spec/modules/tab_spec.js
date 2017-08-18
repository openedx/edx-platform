/*
 * decaffeinate suggestions:
 * DS102: Remove unnecessary code created because of implicit returns
 * Full docs: https://github.com/decaffeinate/decaffeinate/blob/master/docs/suggestions.md
 */
describe('Tab', function() {
  beforeEach(function() {
    loadFixtures('coffee/fixtures/tab.html');
    return this.items = $.parseJSON(readFixtures('coffee/fixtures/items.json'));
  });

  describe('constructor', function() {
    beforeEach(function() {
      spyOn($.fn, 'tabs');
      return this.tab = new Tab(1, this.items);
    });

    it('set the element', function() {
      return expect(this.tab.el).toEqual($('#tab_1'));
    });

    it('build the tabs', function() {
      const links = $('.navigation li>a').map(function() { return $(this).attr('href'); }).get();
      return expect(links).toEqual(['#tab-1-0', '#tab-1-1', '#tab-1-2']);
  });

    it('build the container', function() {
      const containers = $('section').map(function() { return $(this).attr('id'); }).get();
      return expect(containers).toEqual(['tab-1-0', 'tab-1-1', 'tab-1-2']);
  });

    return it('bind the tabs', function() {
      return expect($.fn.tabs).toHaveBeenCalledWith({show: this.tab.onShow});
    });
  });

  // As of jQuery 1.9, the onShow callback is deprecated
  // http://jqueryui.com/upgrade-guide/1.9/#deprecated-show-event-renamed-to-activate
  // The code below tests that onShow does what is expected,
  // but note that onShow will NOT be called when the user
  // clicks on the tab if we're using jQuery version >= 1.9
  return describe('onShow', function() {
    beforeEach(function() {
      this.tab = new Tab(1, this.items);
      return this.tab.onShow($('#tab-1-0'), {'index': 1});
    });

    it('replace content in the container', function() {
      this.tab.onShow($('#tab-1-1'), {'index': 1});
      expect($('#tab-1-0').html()).toEqual('');
      expect($('#tab-1-1').html()).toEqual('Video 2');
      return expect($('#tab-1-2').html()).toEqual('');
    });

    return it('trigger contentChanged event on the element', function() {
      spyOnEvent(this.tab.el, 'contentChanged');
      this.tab.onShow($('#tab-1-1'), {'index': 1});
      return expect('contentChanged').toHaveBeenTriggeredOn(this.tab.el);
    });
  });
});
