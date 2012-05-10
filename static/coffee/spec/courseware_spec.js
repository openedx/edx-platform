(function() {

  describe('Courseware', function() {
    describe('start', function() {
      it('create the navigation', function() {
        spyOn(window, 'Navigation');
        Courseware.start();
        return expect(window.Navigation).toHaveBeenCalled();
      });
      it('create the calculator', function() {
        spyOn(window, 'Calculator');
        Courseware.start();
        return expect(window.Calculator).toHaveBeenCalled();
      });
      it('creates the FeedbackForm', function() {
        spyOn(window, 'FeedbackForm');
        Courseware.start();
        return expect(window.FeedbackForm).toHaveBeenCalled();
      });
      return it('binds the Logger', function() {
        spyOn(Logger, 'bind');
        Courseware.start();
        return expect(Logger.bind).toHaveBeenCalled();
      });
    });
    describe('bind', function() {
      beforeEach(function() {
        this.courseware = new Courseware;
        return setFixtures("<div id=\"seq_content\"></div>");
      });
      return it('binds the sequential content change event', function() {
        this.courseware.bind();
        return expect($('#seq_content')).toHandleWith('contentChanged', this.courseware.render);
      });
    });
    return describe('render', function() {
      beforeEach(function() {
        this.courseware = new Courseware;
        return setFixtures("<div class=\"course-content\">\n  <div id=\"video_1\" class=\"video\" data-streams=\"1.0:abc1234\"></div>\n  <div id=\"video_2\" class=\"video\" data-streams=\"1.0:def5678\"></div>\n</div>");
      });
      return it('detect the video element and convert them', function() {
        spyOn(window, 'Video');
        this.courseware.render();
        expect(window.Video).toHaveBeenCalledWith('1', '1.0:abc1234');
        return expect(window.Video).toHaveBeenCalledWith('2', '1.0:def5678');
      });
    });
  });

}).call(this);
