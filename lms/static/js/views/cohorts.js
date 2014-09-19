(function($, Backbone, CohortEditorView) {
    var CohortsView = Backbone.View.extend({
        events : {
            "change .cohort-select": "showCohortEditor",
            "click .link-cross-reference": "showSection"
        },

        initialize: function() {
            this.template = _.template($('#cohorts-tpl').text());
        },

        render: function() {
            this.$el.html(this.template({
                cohorts: this.model.models
            }));
            return this;
        },

        getSelectedCohort: function() {
            var id = this.$('.cohort-select').val();
            return this.model.get(parseInt(id));
        },

        showCohortEditor: function(event) {
            event.preventDefault();
            var selectedCohort = this.getSelectedCohort();
            this.editor = new CohortEditorView({
                el: this.$('.cohort-management-group'),
                model: selectedCohort
            });
            this.editor.render();
        },

        showSection: function(event) {
            event.preventDefault();
            var section = $(event.currentTarget).data("section");
            $(".instructor-nav .nav-item a[data-section='" + section + "']").click();
        }
    });

    this.CohortsView = CohortsView;
}).call(this, jQuery, Backbone, CohortEditorView);
