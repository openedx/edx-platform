(function() {
  xdescribe('VideoQualityControlAlpha', function() {
    var state, videoControl, videoQualityControl, oldOTBD;

    function initialize() {
      loadFixtures('videoalpha.html');
      state = new VideoAlpha('#example');
      videoControl = state.videoControl;
      videoQualityControl = state.videoQualityControl;
    }

    beforeEach(function() {
      oldOTBD = window.onTouchBasedDevice;
      window.onTouchBasedDevice = jasmine.createSpy('onTouchBasedDevice').andReturn(false);
    });

    afterEach(function() {
      $('source').remove();
      window.onTouchBasedDevice = oldOTBD;
    });

    describe('constructor', function() {
      beforeEach(function() {
        initialize();
      });

      it('render the quality control', function() {
        expect(videoControl.secondaryControlsEl.html()).toContain("<a href=\"#\" class=\"quality_control\" title=\"HD\">");
      });

      it('bind the quality control', function() {
        expect($('.quality_control')).toHandleWith('click', videoQualityControl.toggleQuality);
      });
    });
  });

}).call(this);
