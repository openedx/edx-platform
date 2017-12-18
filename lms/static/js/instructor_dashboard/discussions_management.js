(function() {
    'use strict';

    function DiscussionsManagement($section) {
        this.$section = $section;
        this.$section.data('wrapper', this);
    }

    DiscussionsManagement.prototype.onClickTitle = function() {};

    window.InstructorDashboard.sections.DiscussionsManagement = DiscussionsManagement;
}).call(this);
