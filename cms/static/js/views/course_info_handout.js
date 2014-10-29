define(["js/views/baseview", "codemirror", "js/views/feedback_notification", "js/views/course_info_helper", "js/utils/modal"],
    function(BaseView, CodeMirror, NotificationView, CourseInfoHelper, ModalUtils) {

    // the handouts view is dumb right now; it needs tied to a model and all that jazz
    var CourseInfoHandoutsView = BaseView.extend({
        // collection is CourseUpdateCollection
        events: {
            "click .save-button" : "onSave",
            "click .cancel-button" : "onCancel",
            "click .edit-button" : "onEdit"
        },

        initialize: function() {
            this.template = this.loadTemplate('course_info_handouts');
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
            $('.handouts-content').html(this.model.get('data'));
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

            ModalUtils.showModalCover(false, function() { self.closeEditor() });
        },

        onSave: function(event) {
            $('#handout_error').removeClass('is-shown');
            $('.save-button').removeClass('is-disabled').attr('aria-disabled', false);
            if ($('.CodeMirror-lines').find('.cm-error').length == 0){
                this.model.set('data', this.$codeMirror.getValue());
                var saving = new NotificationView.Mini({
                    title: gettext('Saving')
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
            }else{
                $('#handout_error').addClass('is-shown');
                $('.save-button').addClass('is-disabled').attr('aria-disabled', true);
                event.preventDefault();
            }
        },

        onCancel: function(event) {
            $('#handout_error').removeClass('is-shown');
            $('.save-button').removeClass('is-disabled').attr('aria-disabled', false);
            this.$form.hide();
            this.closeEditor();
        },

        closeEditor: function() {
            $('#handout_error').removeClass('is-shown');
            $('.save-button').removeClass('is-disabled').attr('aria-disabled', false);
            this.$form.hide();
            ModalUtils.hideModalCover();
            this.$form.find('.CodeMirror').remove();
            this.$codeMirror = null;
        }
    });

    return CourseInfoHandoutsView;
}); // end define()
