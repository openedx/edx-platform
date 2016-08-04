// Backbone Application View: Signatory Editor

define([
    'jquery',
    'underscore',
    'backbone',
    'gettext',
    'js/utils/templates',
    'common/js/components/utils/view_utils',
    'common/js/components/views/feedback_prompt',
    'common/js/components/views/feedback_notification',
    'js/models/uploads',
    'js/views/uploads',
    'text!templates/signatory-editor.underscore'
],
function ($, _, Backbone, gettext,
          TemplateUtils, ViewUtils, PromptView, NotificationView, FileUploadModel, FileUploadDialog,
          signatoryEditorTemplate) {
    'use strict';
    var SignatoryEditorView = Backbone.View.extend({
        tagName: 'div',
        events: {
            'change .signatory-name-input': 'setSignatoryName',
            'change .signatory-title-input': 'setSignatoryTitle',
            'change .signatory-organization-input': 'setSignatoryOrganization',
            'click  .signatory-panel-delete': 'deleteItem',
            'change .signatory-signature-input': 'setSignatorySignatureImagePath',
            'click .action-upload-signature': 'uploadSignatureImage'
        },

        className: function () {
            // Determine the CSS class names for this model instance
            var index = this.getModelIndex(this.model);
            return [
                'signatory-edit',
                'signatory-edit-view-' + index
            ].join(' ');
        },

        initialize: function(options) {
            // Set up the initial state of the attributes set for this model instance
             _.bindAll(this, 'render');
            this.model.bind('change', this.render);
            this.eventAgg = options.eventAgg;
            this.isEditingAllCollections = options.isEditingAllCollections;
        },

        getModelIndex: function(givenModel) {
            // Retrieve the position of this model in its collection
            return this.model.collection.indexOf(givenModel);
        },

        loadTemplate: function(name) {
            // Retrieve the corresponding template for this model
            return TemplateUtils.loadTemplate(name);
        },

        getTotalSignatoriesOnServer: function() {
            // Retrieve the count of signatories stored server-side
            var count = 0;
            this.model.collection.each(function( modelSignatory) {
                if(!modelSignatory.isNew()) {
                    count ++;
                }
            });
            return count;
        },

        render: function() {
            // Assemble the editor view for this model
            var attributes = $.extend({
                modelIsValid: this.model.isValid(),
                error: this.model.validationError
            }, this.model.attributes, {
                signatory_number: this.getModelIndex(this.model) + 1,
                signatories_count: this.model.collection.length,
                isNew: this.model.isNew(),
                is_editing_all_collections: this.isEditingAllCollections,
                total_saved_signatories: this.getTotalSignatoriesOnServer()
            });
            return $(this.el).html(_.template(signatoryEditorTemplate)(attributes));
        },

        setSignatoryName: function(event) {
            // Update the model with the provided data
            if (event && event.preventDefault) { event.preventDefault(); }
            this.model.set(
                'name',
                this.$('.signatory-name-input').val(),
                { silent: true }
            );
            this.toggleValidationErrorMessage('name');
            this.eventAgg.trigger("onSignatoryUpdated", this.model);
        },

        setSignatoryTitle: function(event) {
            // Update the model with the provided data
            if (event && event.preventDefault) { event.preventDefault(); }
            this.model.set(
                'title',
                this.$('.signatory-title-input').val(),
                { silent:true }
            );
            this.toggleValidationErrorMessage('title');
            this.eventAgg.trigger("onSignatoryUpdated", this.model);
        },

        setSignatoryOrganization: function(event) {
            // Update the model with the provided data
            if (event && event.preventDefault) { event.preventDefault(); }
            this.model.set(
                'organization',
                this.$('.signatory-organization-input').val(),
                { silent: true }
            );
            this.eventAgg.trigger("onSignatoryUpdated", this.model);
        },

        setSignatorySignatureImagePath: function(event) {
            if (event && event.preventDefault) { event.preventDefault(); }
            this.model.set(
                'signature_image_path',
                this.$('.signatory-signature-input').val(),
                { silent: true }
            );
        },

        deleteItem: function(event) {
            // Remove the specified model from the collection
            if (event && event.preventDefault) { event.preventDefault(); }
            var model = this.model;
            var self = this;
            var titleTextTemplate = _.template(gettext('Delete "<%= signatoryName %>" from the list of signatories?'));
            var confirm = new PromptView.Warning({
                title: titleTextTemplate({signatoryName: model.get('name')}),
                message: gettext('This action cannot be undone.'),
                actions: {
                    primary: {
                        text: gettext('Delete'),
                        click: function () {
                            var deleting = new NotificationView.Mini({
                                title: gettext('Deleting')
                            });
                            if (model.isNew()){
                                model.collection.remove(model);
                                self.eventAgg.trigger("onSignatoryRemoved", model);
                            }
                            else {
                                deleting.show();
                                model.destroy({
                                    wait: true,
                                    success: function (model) {
                                        deleting.hide();
                                        self.eventAgg.trigger("onSignatoryRemoved", model);
                                    }
                                });
                            }
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

        uploadSignatureImage: function(event) {
            event.preventDefault();
            var upload = new FileUploadModel({
                title: gettext("Upload signature image."),
                message: gettext("Image must be in PNG format."),
                mimeTypes: ['image/png']
            });
            var self = this;
            var modal = new FileUploadDialog({
                model: upload,
                onSuccess: function(response) {
                    self.model.set('signature_image_path', response.asset.url);
                }
            });
            modal.show();
        },

        /**
         * @desc Toggle the validation error messages. If given model attribute is not valid then show the error message
         * else remove it.
         * @param string modelAttribute - the attribute of the signatory model e.g. name, title.
        */
        toggleValidationErrorMessage: function(modelAttribute) {
            var selector = "div.add-signatory-" + modelAttribute;
            if (!this.model.isValid() && _.has(this.model.validationError, modelAttribute)) {

                // Show the error message if it is not exist before.
                if( !$(selector).hasClass('error')) {
                    var errorMessage = this.model.validationError[modelAttribute];
                    $(selector).addClass("error");
                    $(selector).append("<span class='message-error'>" + errorMessage + "</span>");
                }
            }
            else {
                // Remove the error message.
                $(selector).removeClass("error");
                $(selector + ">span.message-error").remove();
            }
        }

    });
    return SignatoryEditorView;
});
