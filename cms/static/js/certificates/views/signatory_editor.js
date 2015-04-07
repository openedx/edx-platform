// Backbone Application View: Signatory Editor

define(['js/views/utils/view_utils', "js/views/feedback_prompt", "js/views/feedback_notification", 'js/utils/templates', 'underscore', 'jquery', 'gettext'],
function(ViewUtils, PromptView, NotificationView, TemplateUtils, _, $, gettext) {
    'use strict';
    var SignatoryEditorView = Backbone.View.extend({
        tagName: 'div',
        events: {
            'change .signatory-name-input': 'setSignatoryName',
            'change .signatory-title-input': 'setSignatoryTitle',
            'change .signatory-organization-input': 'setSignatoryOrganization',
            'click  .signatory-panel-delete': 'deleteItem'
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
            this.template = this.loadTemplate('signatory-editor');
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
            return $(this.el).html(this.template(attributes));
        },

        setSignatoryName: function(event) {
            // Update the model with the provided data
            if (event && event.preventDefault) { event.preventDefault(); }
            this.model.set(
                'name',
                this.$('.signatory-name-input').val()
            );
            this.eventAgg.trigger("onSignatoryUpdated", this.model);
        },

        setSignatoryTitle: function(event) {
            // Update the model with the provided data
            if (event && event.preventDefault) { event.preventDefault(); }
            this.model.set(
                'title',
                this.$('.signatory-title-input').val()
            );
            this.eventAgg.trigger("onSignatoryUpdated", this.model);
        },

        setSignatoryOrganization: function(event) {
            // Update the model with the provided data
            if (event && event.preventDefault) { event.preventDefault(); }
            this.model.set(
                'organization',
                this.$('.signatory-organization-input').val()
            );
            this.eventAgg.trigger("onSignatoryUpdated", this.model);
        },

        deleteItem: function(event) {
            // Remove the specified model from the collection
            if (event && event.preventDefault) { event.preventDefault(); }
            var certificate = this.model.get('certificate');
            var model = this.model;
            var self = this;
            var confirm = new PromptView.Warning({
                title: gettext('Are you sure you want to delete "'+model.get('title') +'" as a signatory?'),
                message: gettext('This action cannot be undone.'),
                actions: {
                    primary: {
                        text: gettext('OK'),
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
                                    success: function (model, response) {
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
        }
    });
    return SignatoryEditorView;
});
