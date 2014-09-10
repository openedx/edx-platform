(function(Backbone, CohortEditorView) {
    var CohortsView = Backbone.View.extend({
        events : {
            "change .cohort-select": "showCohortEditor"
        },

        initialize: function(options) {
            this.template = _.template($('#cohorts-tpl').text());
            this.selectorTemplate = _.template($('#cohort-selector-tpl').text());
            this.advanced_settings_url = options.advanced_settings_url;
            this.model.on('sync', this.onSync, this);
        },

        render: function() {
            this.$el.html(this.template({
                cohorts: this.model.models
            }));
            this.renderSelector();
            return this;
        },

        renderSelector: function(selectedCohort) {
            this.$('.cohort-select').html(this.selectorTemplate({
                cohorts: this.model.models,
                selectedCohort: selectedCohort
            }));
        },

        onSync: function() {
            this.renderSelector(this.getSelectedCohort());
        },

        getSelectedCohort: function() {
            var id = this.$('.cohort-select').val();
            return id && this.model.get(parseInt(id));
        },

        showCohortEditor: function(event) {
            event.preventDefault();
            var selectedCohort = this.getSelectedCohort();
            if (this.editor) {
                this.editor.setCohort(selectedCohort);
            } else {
                this.editor = new CohortEditorView({
                    el: this.$('.cohort-management-group'),
                    model: selectedCohort,
                    cohorts: this.model,
                    advanced_settings_url: this.advanced_settings_url
                });
                this.editor.render();
            }
        }
    });

    this.CohortsView = CohortsView;
}).call(this, Backbone, CohortEditorView);
