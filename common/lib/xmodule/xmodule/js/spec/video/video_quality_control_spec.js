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
      window.onTouchBasedDevice = jasmine.createSpy('onTouchBasedDevice').andReturn(false);
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

      // Disabled when ARIA markup was added to the anchor
      it('render the quality control', function() {
        expect(videoControl.secondaryControlsEl.html())
          .toContain(
            '<a ' +
              'href="#" ' +
              'class="quality_control" ' +
              'title="HD" ' +
              'role="button" ' +
              'aria-disabled="false"' +
            '>HD</a>'
          );
      });

      it('bind the quality control', function() {
        expect($('.quality_control'))
          .toHandleWith('click', videoQualityControl.toggleQuality);
      });
    });
  });

}).call(this);
