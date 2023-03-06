define([
    'js/views/baseview',
    'codemirror',
    'common/js/components/views/feedback_notification',
    'js/views/course_info_helper',
    'js/utils/modal',
    'edx-ui-toolkit/js/utils/html-utils'
],
function(BaseView, CodeMirror, NotificationView, CourseInfoHelper, ModalUtils, HtmlUtils) {
    'use strict';
    // the handouts view is dumb right now; it needs tied to a model and all that jazz
    var CourseInfoHandoutsView = BaseView.extend({
    // collection is CourseUpdateCollection
        events: {
            'click .save-button': 'onSave',
            'click .cancel-button': 'onCancel',
            'click .edit-button': 'onEdit'
        },

        initialize: function() {
            var self = this;
            this.template = this.loadTemplate('course_info_handouts');
            this.model.fetch({
                complete: function() {
                    self.render();
                },
                reset: true
            });
        },

        render: function() {
            CourseInfoHelper.changeContentToPreview(
                this.model, 'data', this.options.base_asset_url);
            this.$el.html(HtmlUtils.HTML($(this.template({model: this.model}))).toString());
            HtmlUtils.setHtml($('.handouts-content'), HtmlUtils.HTML(this.model.get('data')));
            this.$preview = this.$el.find('.handouts-content');
            this.$form = this.$el.find('.edit-handouts-form');
            this.$editor = this.$form.find('.handouts-content-editor');
            this.$form.hide();

            return this;
        },

        onEdit: function() {
            var self = this;
            this.$editor.val(this.$preview.html());
            this.$form.show();

            this.$codeMirror = CourseInfoHelper.editWithCodeMirror(
                self.model, 'data', self.options.base_asset_url, this.$editor.get(0));

            ModalUtils.showModalCover(false, function() { self.closeEditor(); });
        },

        onSave: function(event) {
            var saving = new NotificationView.Mini({
                title: gettext('Saving')
            });
            var handoutsContent = this.$codeMirror.getValue();
            $('#handout_error').removeClass('is-shown');
            $('.save-button').removeClass('is-disabled').attr('aria-disabled', false);
            if ($('.CodeMirror-lines').find('.cm-error').length === 0) {
                if (handoutsContent === '') {
                    handoutsContent = '<ol></ol>';
                }
                this.model.set('data', handoutsContent);
                saving.show();
                this.model.save({}, {
                    success: function() {
                        saving.hide();
                    }
                });
                this.render();
                this.$form.hide();
                this.closeEditor();

                analytics.track('Saved Course Handouts', { // eslint-disable-line no-undef
                    course: course_location_analytics // eslint-disable-line no-undef
                });
            } else {
                $('#handout_error').addClass('is-shown');
                $('.save-button').addClass('is-disabled').attr('aria-disabled', true);
                event.preventDefault();
            }
        },

        onCancel: function() {
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
