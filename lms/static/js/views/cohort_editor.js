(function(Backbone) {
    var CohortEditorView = Backbone.View.extend({
        events : {
            "click .form-submit": "addStudents"
        },

        initialize: function() {
            this.template = _.template($('#cohort-editor-tpl').text());
        },

        render: function() {
            this.$el.html(this.template({
                cohort: this.model
            }));
            return this;
        },

        addStudents: function(event) {
            event.preventDefault();
            var input = this.$('.cohort-management-group-add-students'),
                add_url = this.model.url() + '/add',
                data = {'users': input.val()};
            $.post(add_url, data).done(function() {
                window.alert('done it!');
            });
        }
    });

    this.CohortEditorView = CohortEditorView;
}).call(this, Backbone);
