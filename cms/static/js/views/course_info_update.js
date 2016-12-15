define(["js/views/baseview", "codemirror", "js/models/course_update",
        "common/js/components/views/feedback_prompt", "common/js/components/views/feedback_notification",
        "js/views/course_info_helper", "js/utils/modal", "common/js/components/utils/view_utils"],
    function(BaseView, CodeMirror, CourseUpdateModel, PromptView, NotificationView, CourseInfoHelper, ModalUtils, ViewUtils) {

    var CourseInfoUpdateView = BaseView.extend({

        // collection is CourseUpdateCollection
        events: {
            "click .new-update-button" : "onNew",
            "click #course-update-view .save-button" : "onSave",
            "click #course-update-view .cancel-button" : "onCancel",
            "click .post-actions > .edit-button" : "onEdit",
            "click .post-actions > .delete-button" : "onDelete"
        },

        initialize: function() {
            this.template = this.loadTemplate('course_info_update');
            this.render();
            // when the client refetches the updates as a whole, re-render them
            this.listenTo(this.collection, 'reset', this.render);
        },

        render: function () {
            // iterate over updates and create views for each using the template
            var updateEle = this.$el.find("#course-update-list");
            // remove and then add all children
            $(updateEle).empty();
            var self = this;
            this.collection.each(function (update) {
                try {
                    CourseInfoHelper.changeContentToPreview(
                        update, 'content', self.options['base_asset_url']);
                    // push notification is always disabled for existing updates
                    var newEle = self.template({ updateModel : update, push_notification_enabled : false });
                    $(updateEle).append(newEle);
                } catch (e) {
                    // ignore
                }
            });
            this.$el.find(".new-update-form").hide();
            this.$el.find('.date').datepicker({ 'dateFormat': 'MM d, yy' });
            return this;
        },

        onNew: function(event) {
            event.preventDefault();
            var self = this;
            // create new obj, insert into collection, and render this one ele overriding the hidden attr
            var newModel = new CourseUpdateModel();
            this.collection.add(newModel, {at : 0});

            var $newForm = $(
                this.template({
                    updateModel : newModel,
                    push_notification_enabled : this.options.push_notification_enabled
                })
            );

            var updateEle = this.$el.find("#course-update-list");
            $(updateEle).prepend($newForm);

            var $textArea = $newForm.find(".new-update-content").first();
            this.$codeMirror = CodeMirror.fromTextArea($textArea.get(0), {
                mode: "text/html",
                lineNumbers: true,
                lineWrapping: true
            });

            $newForm.addClass('editing');
            this.$currentPost = $newForm.closest('li');

            // Variable stored for unit test.
            this.$modalCover = ModalUtils.showModalCover(false, function() {
                // Binding empty function to prevent default hideModal.
            });

            $('.date').datepicker('destroy');
            $('.date').datepicker({ 'dateFormat': 'MM d, yy' });
        },

        onSave: function(event) {
            event.preventDefault();
            var validation = ViewUtils.keywordValidator.validateString(this.$codeMirror.getValue());
            if (!validation.isValid) {
                message = gettext('There are invalid keywords in your message. Please check the following keywords and try again:');
                message += "\n" + validation.keywordsInvalid.join('\n');
                window.alert(message);
                return;
            }
            var targetModel = this.eventModel(event);
            targetModel.set({
                date : this.dateEntry(event).val(),
                content : this.$codeMirror.getValue(),
                push_notification_selected : this.push_notification_selected(event)
            });
            // push change to display, hide the editor, submit the change
            var saving = new NotificationView.Mini({
                title: gettext('Saving')
            });
            saving.show();
            var ele = this.modelDom(event);
            targetModel.save({}, {
                success: function() {
                    saving.hide();
                },
                error: function() {
                    ele.remove();
                }
            });
            this.closeEditor(false);

            analytics.track('Saved Course Update', {
                'course': course_location_analytics,
                'date': this.dateEntry(event).val(),
                'push_notification_selected': this.push_notification_selected(event)
            });
        },

        onCancel: function(event) {
            event.preventDefault();
            // change editor contents back to model values and hide the editor
            $(this.editor(event)).hide();
            // If the model was never created (user created a new update, then pressed Cancel),
            // we wish to remove it from the DOM.
            var targetModel = this.eventModel(event);
            this.closeEditor(!targetModel.id);
        },

        onEdit: function(event) {
            event.preventDefault();
            var self = this;
            this.$currentPost = $(event.target).closest('li');
            this.$currentPost.addClass('editing');

            $(this.editor(event)).show();
            var $textArea = this.$currentPost.find(".new-update-content").first();
            var targetModel = this.eventModel(event);
            this.$codeMirror = CourseInfoHelper.editWithCodeMirror(
                targetModel, 'content', self.options['base_asset_url'], $textArea.get(0));

            // Variable stored for unit test.
            this.$modalCover = ModalUtils.showModalCover(false,
                function() {
                    self.closeEditor(false);
                }
            );
        },

        onDelete: function(event) {
            event.preventDefault();

            var self = this;
            var targetModel = this.eventModel(event);
            var confirm = new PromptView.Warning({
                title: gettext('Are you sure you want to delete this update?'),
                message: gettext('This action cannot be undone.'),
                actions: {
                    primary: {
                        text: gettext('OK'),
                        click: function () {
                            analytics.track('Deleted Course Update', {
                                'course': course_location_analytics,
                                'date': self.dateEntry(event).val()
                            });
                            self.modelDom(event).remove();
                            var deleting = new NotificationView.Mini({
                                title: gettext('Deleting')
                            });
                            deleting.show();
                            targetModel.destroy({
                                success: function (model, response) {
                                    self.collection.fetch({
                                        success: function() {
                                            self.render();
                                            deleting.hide();
                                        },
                                        reset: true
                                    });
                                }
                            });
                            confirm.hide();
                        }
                    },
                    secondary: {
                        text: gettext('Cancel'),
                        click: function() {
                            confirm.hide();
                        }
                    }
                }
            });
            confirm.show();
        },

        closeEditor: function(removePost) {
            var targetModel = this.collection.get(this.$currentPost.attr('name'));

            if(removePost) {
                this.$currentPost.remove();
            }
            else {
                // close the modal and insert the appropriate data
                this.$currentPost.removeClass('editing');
                this.$currentPost.find('.date-display').html(targetModel.get('date'));
                this.$currentPost.find('.date').val(targetModel.get('date'));

                var content = CourseInfoHelper.changeContentToPreview(
                    targetModel, 'content', this.options['base_asset_url']);
                try {
                    // just in case the content causes an error (embedded js errors)
                    this.$currentPost.find('.update-contents').html(content);
                    this.$currentPost.find('.new-update-content').val(content);
                } catch (e) {
                    // ignore but handle rest of page
                }
                this.$currentPost.find('form').hide();
                this.$currentPost.find('.CodeMirror').remove();

                // hide the push notification checkbox for subsequent edits to the Post
                var push_notification_ele = this.$currentPost.find(".new-update-push-notification");
                if (push_notification_ele) {
                    push_notification_ele.hide();
                }
            }

            ModalUtils.hideModalCover(this.$modalCover);
            this.$codeMirror = null;
        },

        // Dereferencing from events to screen elements
        eventModel: function(event) {
            // not sure if it should be currentTarget or delegateTarget
            return this.collection.get($(event.currentTarget).attr("name"));
        },

        modelDom: function(event) {
            return $(event.currentTarget).closest("li");
        },

        editor: function(event) {
            var li = $(event.currentTarget).closest("li");
            if (li) {
                return $(li).find("form").first();
            }
        },

        dateEntry: function(event) {
            var li = $(event.currentTarget).closest("li");
            if (li) {
                return $(li).find(".date").first();
            }
        },

        push_notification_selected: function(event) {
            var push_notification_checkbox;
            var li = $(event.currentTarget).closest("li");
            if (li) {
                push_notification_checkbox = li.find(".new-update-push-notification .toggle-checkbox");
                if (push_notification_checkbox) {
                    return push_notification_checkbox.is(":checked");
                }
            }
        }
    });

    return CourseInfoUpdateView;
}); // end define()
