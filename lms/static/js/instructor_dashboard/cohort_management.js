(function() {
  var CohortManagement;

  CohortManagement = (function() {

    function CohortManagement($section) {
      this.$section = $section;
      this.$section.data('wrapper', this);
    }

    CohortManagement.prototype.onClickTitle = function() {};

    return CohortManagement;

  })();

  _.defaults(window, {
    InstructorDashboard: {}
  });

  _.defaults(window.InstructorDashboard, {
    sections: {}
  });

  _.defaults(window.InstructorDashboard.sections, {
    CohortManagement: CohortManagement
  });

}).call(this);
