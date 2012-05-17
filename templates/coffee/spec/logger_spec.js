(function() {

  describe('Logger', function() {
    it('expose window.log_event', function() {
      jasmine.stubRequests();
      return expect(window.log_event).toBe(Logger.log);
    });
    describe('log', function() {
      return it('send a request to log event', function() {
        spyOn($, 'getWithPrefix');
        Logger.log('example', 'data');
        return expect($.getWithPrefix).toHaveBeenCalledWith('/event', {
          event_type: 'example',
          event: '"data"',
          page: window.location.href
        });
      });
    });
    return describe('bind', function() {
      beforeEach(function() {
        Logger.bind();
        return Courseware.prefix = '/6002x';
      });
      afterEach(function() {
        return window.onunload = null;
      });
      it('bind the onunload event', function() {
        return expect(window.onunload).toEqual(jasmine.any(Function));
      });
      return it('send a request to log event', function() {
        spyOn($, 'ajax');
        $(window).trigger('onunload');
        return expect($.ajax).toHaveBeenCalledWith({
          url: "" + Courseware.prefix + "/event",
          data: {
            event_type: 'page_close',
            event: '',
            page: window.location.href
          },
          async: false
        });
      });
    });
  });

}).call(this);
