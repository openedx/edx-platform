(function(Backbone) {
    var CohortEditorView = Backbone.View.extend({
        initialize: function() {
            this.template = _.template($('#cohort-editor-tpl').text());
        },

        render: function() {
            this.$el.html(this.template({
                cohort: this.model
            }));
            return this;
        }
    });

    this.CohortEditorView = CohortEditorView;
}).call(this, Backbone);
