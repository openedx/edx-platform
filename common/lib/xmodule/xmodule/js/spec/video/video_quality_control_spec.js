(function() {
  describe('VideoQualityControl', function() {
    var state, videoControl, videoQualityControl, oldOTBD;

    function initialize() {
      loadFixtures('video.html');
      state = new Video('#example');
      videoControl = state.videoControl;
      videoQualityControl = state.videoQualityControl;
    }

    beforeEach(function() {
      oldOTBD = window.onTouchBasedDevice;
      window.onTouchBasedDevice = jasmine
                                      .createSpy('onTouchBasedDevice')
                                      .andReturn(null);
    });

    afterEach(function() {
      $('source').remove();
      window.onTouchBasedDevice = oldOTBD;
    });

    describe('constructor', function() {
      var oldYT = window.YT;

      beforeEach(function() {
        window.YT = {
            Player: function () { },
            PlayerState: oldYT.PlayerState,
            ready: function(f){f();}
        };

        initialize();
      });

      afterEach(function () {
        window.YT = oldYT;
      });

      it('render the quality control', function() {
        var container = videoControl.secondaryControlsEl;
        expect(container).toContain('a.quality_control');
      });

      it('add ARIA attributes to quality control', function () {
        var qualityControl = $('a.quality_control');
        expect(qualityControl).toHaveAttrs({
          'role': 'button',
          'title': 'HD off',
          'aria-disabled': 'false'
        });
      });

      it('bind the quality control', function() {
        var handler = videoQualityControl.toggleQuality;
        expect($('a.quality_control')).toHandleWith('click', handler);
      });
    });
  });

}).call(this);
