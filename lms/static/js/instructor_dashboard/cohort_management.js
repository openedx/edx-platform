(function() {
    var CohortManagement;

    CohortManagement = (function() {
        function CohortManagement($section) {
            this.$section = $section;
            this.$section.data('wrapper', this);
        }

        CohortManagement.prototype.onClickTitle = function() {};

        return CohortManagement;
    }());

    window.InstructorDashboard.sections.CohortManagement = CohortManagement;
}).call(this);
