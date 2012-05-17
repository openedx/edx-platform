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
        return setFixtures("<div class=\"course-content\">\n  <div class=\"sequence\"></div>\n</div>");
      });
      return it('binds the content change event', function() {
        this.courseware.bind();
        return expect($('.course-content .sequence')).toHandleWith('contentChanged', this.courseware.render);
      });
    });
    return describe('render', function() {
      beforeEach(function() {
        jasmine.stubRequests();
        this.courseware = new Courseware;
        spyOn(window, 'Histogram');
        spyOn(window, 'Problem');
        spyOn(window, 'Video');
        setFixtures("<div class=\"course-content\">\n  <div id=\"video_1\" class=\"video\" data-streams=\"1.0:abc1234\"></div>\n  <div id=\"video_2\" class=\"video\" data-streams=\"1.0:def5678\"></div>\n  <div id=\"problem_3\" class=\"problems-wrapper\" data-url=\"/example/url/\">\n    <div id=\"histogram_3\" class=\"histogram\" data-histogram=\"[[0, 1]]\" style=\"height: 20px; display: block;\">\n  </div>\n</div>");
        return this.courseware.render();
      });
      it('detect the video elements and convert them', function() {
        expect(window.Video).toHaveBeenCalledWith('1', '1.0:abc1234');
        return expect(window.Video).toHaveBeenCalledWith('2', '1.0:def5678');
      });
      it('detect the problem element and convert it', function() {
        return expect(window.Problem).toHaveBeenCalledWith('3', '/example/url/');
      });
      return it('detect the histrogram element and convert it', function() {
        return expect(window.Histogram).toHaveBeenCalledWith('3', [[0, 1]]);
      });
    });
  });

}).call(this);
