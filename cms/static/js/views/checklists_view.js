if (!CMS.Views['Checklists']) CMS.Views.Checklists = {};

CMS.Views.Checklists = Backbone.View.extend({
    // takes CMS.Models.Checklists as model

    events : {
        'click .course-checklist .checklist-title' : "toggleChecklist",
        'click .course-checklist .task label' : "toggleTask",
        'click .demo-checklistviz' : "demoUpdateProgress"
    },

    initialize : function() {
        // adding class and title needs to happen in HTML
//        $('.course-checklist .checklist-title').each(function(e){
//            $(this).addClass('is-selectable').attr('title','Collapse/Expand this Checklist').bind('click', this.toggleChecklist);
//        });
    },

    toggleChecklist : function(e) {
        (e).preventDefault();
        $(e.target).closest('.course-checklist').toggleClass('is-collapsed');
    },

    toggleTask : function (e) {
        (e).preventDefault();
        $(e.target).closest('.task').toggleClass('is-completed');
    },

    // TODO: remove
    demoUpdateProgress : function(e) {
        (e).preventDefault();
        $('#course-checklist0 .viz-checklist-status .viz-checklist-status-value').css('width','25%');
    },

    // TODO: not used. In-progress update checklist progress (based on checkbox check/uncheck events)
    updateChecklistProgress : function(e) {
        var $statusCount = this.$el.closest('.course-checklist').find('.status-count');
        var $statusAmount = this.$el.closest('.course-checklist').find('.status-amount');

        if (this.$el.attr('checked')) {
            console.log('adding');
        }

        else {
            console.log('subtracting');
        }
    }

});