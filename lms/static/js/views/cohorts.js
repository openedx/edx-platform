(function(Backbone, CohortEditorView) {
    var CohortsView = Backbone.View.extend({
        events : {
            "change .cohort-select": "showCohortEditor"
        },

        initialize: function(options) {
            this.template = _.template($('#cohorts-tpl').text());
            this.advanced_settings_url = options.advanced_settings_url;
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
                model: selectedCohort,
                advanced_settings_url: this.advanced_settings_url
            });
            this.editor.render();
        }
    });

    this.CohortsView = CohortsView;
}).call(this, Backbone, CohortEditorView);
