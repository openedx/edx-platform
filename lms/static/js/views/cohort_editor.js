(function(Backbone) {
    var CohortEditorView = Backbone.View.extend({
        initialize: function(options) {
            this.template = _.template($('#cohort-editor-tpl').text());
            this.advanced_settings_url = options.advanced_settings_url;
        },

        render: function() {
            this.$el.html(this.template({
                cohort: this.model,
                advanced_settings_url: this.advanced_settings_url
            }));
            return this;
        }
    });

    this.CohortEditorView = CohortEditorView;
}).call(this, Backbone);
