/* globals _, edx */

(function($, _) {  // eslint-disable-line wrap-iife
    'use strict';
    var CanvasIntegration = (function() {
      function InstructorDashboardCanvasIntegration($section) {
        var canvasIntegrationObj = this;
        this.$section = $section;
        this.$section.data('wrapper', this);

        this.$add_enrollments_using_canvas_btn = this.$section.find(
          "input[name='add-enrollments-using-canvas']"
        );

        this.$add_enrollments_using_canvas_btn.click(function (event) {
          var $el = $(event.target);
          var url = $el.data('endpoint');
          return $.ajax({
            type: 'POST',
            dataType: 'json',
            url: url,
          });
        });
      }
      InstructorDashboardCanvasIntegration.prototype.onClickTitle = function() {};

      return InstructorDashboardCanvasIntegration
    })();

    _.defaults(window, {
        InstructorDashboard: {}
    });

    _.defaults(window.InstructorDashboard, {
        sections: {}
    });

    _.defaults(window.InstructorDashboard.sections, {
        CanvasIntegration: CanvasIntegration
    });
}).call(this, $, _);
