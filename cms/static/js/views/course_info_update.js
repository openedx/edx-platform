define(['codemirror',
    'js/utils/modal',
    'js/utils/date_utils',
    'edx-ui-toolkit/js/utils/html-utils',
    'js/views/course_info_helper',
    'js/views/validation',
    'js/models/course_update',
    'common/js/components/views/feedback_prompt',
    'common/js/components/views/feedback_notification'],
    function(CodeMirror, ModalUtils, DateUtils, HtmlUtils, CourseInfoHelper, ValidatingView, CourseUpdateModel,
             PromptView, NotificationView) {
        'use strict';
        var CourseInfoUpdateView = ValidatingView.extend({

        // collection is CourseUpdateCollection
            events: {
                'click .new-update-button': 'onNew',
                'click .save-button': 'onSave',
                'click .cancel-button': 'onCancel',
                'click .post-actions > .edit-button': 'onEdit',
                'click .post-actions > .delete-button': 'onDelete'
            },

            initialize: function() {
                this.template = this.loadTemplate('course_info_update');

                // when the client refetches the updates as a whole, re-render them
                this.listenTo(this.collection, 'reset', this.render);
                this.listenTo(this.collection, 'invalid', this.handleValidationError);
            },

            render: function() {
                // iterate over updates and create views for each using the template
                var updateList = this.$el.find('#course-update-list'),
                    self = this;
                $(updateList).empty();
                if (this.collection.length > 0) {
                    this.collection.each(function(update, index) {
                        try {
                            CourseInfoHelper.changeContentToPreview(
                                update, 'content', self.options.base_asset_url);
                            HtmlUtils.append(
                                updateList,
                                HtmlUtils.HTML(self.template({updateModel: update}))
                            );
                            DateUtils.setupDatePicker('date', self, index);
                            update.isValid();
                        } catch (e) {
                            // ignore
                        } finally {
                            if (index === self.collection.length - 1) {
                                // Once the collection is loaded enable the button.
                                self.$el.find('.new-update-button').removeAttr('disabled');
                            }
                        }
                    });
                } else {
                    // If the collection is empty enable the New update button
                    self.$el.find('.new-update-button').removeAttr('disabled');
                }

                // Hide Update forms that are not for new updates with the editing class
                updateList.children().each(function(index, updateElement) {
                    var $updateElement = $(updateElement);
                    var updateForm = $updateElement.find('.new-update-form');
                    if ($updateElement.length > 0 && !$updateElement.hasClass('editing')) {
                        $(updateForm).hide();
                    }
                });
                return this;
            },

            collectionSelector: function(uid) {
                return 'course-update-list li[name=' + uid + ']';
            },

            setAndValidate: function(attr, value, event) {
                if (attr === 'date') {
                // If the value to be set was typed, validate that entry rather than the current datepicker value
                    if (this.dateEntry(event).length > 0) {
                        value = DateUtils.parseDateFromString(this.dateEntry(event).val());
                        if (value && isNaN(value.getTime())) {
                            value = '';
                        }
                    }
                    value = $.datepicker.formatDate('MM d, yy', value);
                }
                var targetModel = this.collection.get(this.$currentPost.attr('name'));
                var prevValue = targetModel.get(attr);
                if (prevValue !== value) {
                    targetModel.set(attr, value);
                    this.validateModel(targetModel);
                }
            },

            handleValidationError: function(model, error) {
                var self = this,
                    $validationElement = this.$el.find('#course-update-list li[name="' + model.cid + '"]');

                $validationElement.find('.message-error').remove();
                Object.keys(error).forEach(function(field) {
                    if (error.hasOwnProperty(field)) {
                        HtmlUtils.append(
                            $validationElement.find('#update-date-' + model.cid).parent(),
                            self.errorTemplate({message: error[field]})
                        );
                        HtmlUtils.append(
                            $validationElement.find('.date-display').parent(),
                            self.errorTemplate({message: error[field]})
                        );
                    }
                });

                $validationElement.find('.save-button').addClass('is-disabled');
            },

            validateModel: function(model) {
                var $validationElement = this.$el.find('#course-update-list li[name="' + model.cid + '"]');
                if (model.isValid()) {
                    $validationElement.find('.message-error').remove();
                    $validationElement.find('.save-button').removeClass('is-disabled');
                }
            },

            onNew: function(event) {
                // create new obj, insert into collection, and render this one ele overriding the hidden attr
                var newModel = new CourseUpdateModel();
                event.preventDefault();

                this.collection.add(newModel, {at: 0});

                var $newForm = $(
                this.template({
                    updateModel: newModel
                })
                );

                var updateEle = this.$el.find('#course-update-list');
                $(updateEle).prepend($newForm);

                var $textArea = $newForm.find('.new-update-content').first();
                this.$codeMirror = CodeMirror.fromTextArea($textArea.get(0), {
                    mode: 'text/html',
                    lineNumbers: true,
                    lineWrapping: true
                });

                $newForm.addClass('editing');
                this.$currentPost = $newForm.closest('li');

                // Variable stored for unit test.
                this.$modalCover = ModalUtils.showModalCover(false, function() {
                // Binding empty function to prevent default hideModal.
                });

                DateUtils.setupDatePicker('date', this, 0);
            },

            onSave: function(event) {
                event.preventDefault();
                var targetModel = this.eventModel(event);
                targetModel.set({
                // translate short-form date (for input) into long form date (for display)
                    date: $.datepicker.formatDate('MM d, yy', new Date(this.dateEntry(event).val())),
                    content: this.$codeMirror.getValue()
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
                    course: course_location_analytics,
                    date: this.dateEntry(event).val()
                });
            },

            onCancel: function(event) {
                event.preventDefault();
            // Since we're cancelling, the model should be using it's previous attributes
                var targetModel = this.eventModel(event);
                targetModel.set(targetModel.previousAttributes());
                this.validateModel(targetModel);
            // Hide the editor
                $(this.editor(event)).hide();
            // targetModel will be lacking an id if it was newly created
                this.closeEditor(!targetModel.id);
            },

            onEdit: function(event) {
                event.preventDefault();
                var self = this;
                this.$currentPost = $(event.target).closest('li');
                this.$currentPost.addClass('editing');

                $(this.editor(event)).show();
                var $textArea = this.$currentPost.find('.new-update-content').first();
                var targetModel = this.eventModel(event);
            // translate long-form date (for viewing) into short-form date (for input)
                if (targetModel.get('date') && targetModel.isValid()) {
                    $(this.dateEntry(event)).val($.datepicker.formatDate('mm/dd/yy', new Date(targetModel.get('date'))));
                } else {
                    $(this.dateEntry(event)).val('MM/DD/YY');
                }
                this.$codeMirror = CourseInfoHelper.editWithCodeMirror(
                targetModel, 'content', self.options.base_asset_url, $textArea.get(0));

            // Variable stored for unit test.
                this.$modalCover = ModalUtils.showModalCover(false,
                function() {
                    self.closeEditor(false);
                }
            );

            // Ensure validity is marked appropriately
                targetModel.isValid();
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
                            click: function() {
                                analytics.track('Deleted Course Update', {
                                    course: course_location_analytics,
                                    date: self.dateEntry(event).val()
                                });
                                self.modelDom(event).remove();
                                var deleting = new NotificationView.Mini({
                                    title: gettext('Deleting')
                                });
                                deleting.show();
                                targetModel.destroy({
                                    success: function() {
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
                var content,
                    targetModel = this.collection.get(this.$currentPost.attr('name'));

            // If the model was never created (user created a new update, then pressed Cancel),
            // we wish to remove it from the DOM.
                if (removePost) {
                    this.$currentPost.remove();
                } else {
                // close the modal and insert the appropriate data
                    this.$currentPost.removeClass('editing');
                    this.$currentPost.find('.date-display').text(targetModel.get('date'));
                    this.$currentPost.find('.date').val(targetModel.get('date'));

                    content = HtmlUtils.HTML(CourseInfoHelper.changeContentToPreview(
                        targetModel, 'content', this.options.base_asset_url
                    ));
                    try {
                    // just in case the content causes an error (embedded js errors)
                        HtmlUtils.setHtml(this.$currentPost.find('.update-contents'), content);
                        this.$currentPost.find('.new-update-content').val(content);
                    } catch (e) {
                    // ignore but handle rest of page
                    }
                    this.$currentPost.find('form').hide();
                    this.$currentPost.find('.CodeMirror').remove();
                }

                ModalUtils.hideModalCover(this.$modalCover);
                this.$codeMirror = null;
            },

        // Dereferencing from events to screen elements
            eventModel: function(event) {
            // not sure if it should be currentTarget or delegateTarget
                return this.collection.get($(event.currentTarget).attr('name'));
            },

            modelDom: function(event) {
                return $(event.currentTarget).closest('li');
            },

            editor: function(event) {
                var li = $(event.currentTarget).closest('li');
                if (li) {
                    return $(li).find('form').first();
                }
            },

            dateEntry: function(event) {
                var li = $(event.currentTarget).closest('li');
                if (li) {
                    return $(li).find('.date').first();
                }
            }
        });

        return CourseInfoUpdateView;
    }); // end define()
