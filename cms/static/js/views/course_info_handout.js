define(["backbone", "underscore", "codemirror", "js/views/feedback_notification", "js/views/course_info_helper"],
    function(Backbone, _, CodeMirror, NotificationView, CourseInfoHelper) {

    var $modalCover = $(".modal-cover");
    // the handouts view is dumb right now; it needs tied to a model and all that jazz
    var CourseInfoHandoutsView = Backbone.View.extend({
        // collection is CourseUpdateCollection
        events: {
            "click .save-button" : "onSave",
            "click .cancel-button" : "onCancel",
            "click .edit-button" : "onEdit"
        },

        initialize: function() {
            this.template = _.template($("#course_info_handouts-tpl").text());
            var self = this;
            this.model.fetch({
                complete: function() {
                    self.render();
                },
                reset: true
            });
        },

        render: function () {
            CourseInfoHelper.changeContentToPreview(
                this.model, 'data', this.options['base_asset_url']);

            this.$el.html(
                $(this.template({
                    model: this.model
                }))
            );
            this.$preview = this.$el.find('.handouts-content');
            this.$form = this.$el.find(".edit-handouts-form");
            this.$editor = this.$form.find('.handouts-content-editor');
            this.$form.hide();

            return this;
        },

        onEdit: function(event) {
            var self = this;
            this.$editor.val(this.$preview.html());
            this.$form.show();

            this.$codeMirror = CourseInfoHelper.editWithCodeMirror(
                self.model, 'data', self.options['base_asset_url'], this.$editor.get(0));

            $modalCover.show();
            $modalCover.bind('click', function() {
                self.closeEditor();
            });
        },

        onSave: function(event) {
            this.model.set('data', this.$codeMirror.getValue());
            var saving = new NotificationView.Mini({
                title: gettext('Saving&hellip;')
            });
            saving.show();
            this.model.save({}, {
                success: function() {
                    saving.hide();
                }
            });
            this.render();
            this.$form.hide();
            this.closeEditor();

            analytics.track('Saved Course Handouts', {
                'course': course_location_analytics
            });

        },

        onCancel: function(event) {
            this.$form.hide();
            this.closeEditor();
        },

        closeEditor: function() {
            this.$form.hide();
            $modalCover.unbind('click');
            $modalCover.hide();
            this.$form.find('.CodeMirror').remove();
            this.$codeMirror = null;
        }
    });

    return CourseInfoHandoutsView;
}); // end define()
