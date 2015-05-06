/**
 * This class defines an editing view for course certificates.
 * It is expected to be backed by a Certificate model.
 */
define(['js/views/utils/view_utils', "js/views/feedback_prompt", "js/views/feedback_notification", 'js/utils/templates', 'underscore', 'jquery', 'gettext'],
function(ViewUtils, PromptView, NotificationView, TemplateUtils, _, $, gettext) {
    'use strict';
    console.log('certificate_editor.start');
    var SignatoryEditorView = Backbone.View.extend({
        tagName: 'div',
        events: {
            'change .signatory-name-input': 'setSignatoryName',
            'change .signatory-title-input': 'setSignatoryTitle',
            'click  .signatory-panel-delete': 'deleteItem'
        },

        className: function () {
            console.log('signatory_editor.className');
            var index = this.getModelIndex(this.model);

            return [
                'signatory-edit',
                'signatory-edit-view-' + index
            ].join(' ');
        },

        initialize: function(options) {
             _.bindAll(this, 'render');
            this.model.bind('change', this.render);
            this.eventAgg = options.eventAgg;
            this.isEditingAllCollections = options.isEditingAllCollections;
            this.template = this.loadTemplate('signatory-editor');
        },

        /**
         * Get the model index/position in its collection.
         */
        getModelIndex: function(givenModel) {
            return this.model.collection.indexOf(givenModel);
        },

        loadTemplate: function(name) {
            return TemplateUtils.loadTemplate(name);
        },

        /**
         * Get the count of signatories that are saved on server.
         */
        getTotalSignatoriesOnServer: function() {
            var count = 0;
            this.model.collection.each(function( modelSignatory) {
                if(!modelSignatory.isNew()) {
                    count ++;
                }
            });
            return count;
        },

        render: function() {
            var attributes = $.extend({}, this.model.attributes, {
                signatory_number: this.getModelIndex(this.model) + 1,
                signatories_count: this.model.collection.length,
                isNew: this.model.isNew(),
                is_editing_all_collections: this.isEditingAllCollections,
                total_saved_signatories: this.getTotalSignatoriesOnServer()
            });

            return $(this.el).html(this.template(attributes));
        },

        setSignatoryName: function(event) {
            if (event && event.preventDefault) { event.preventDefault(); }
            this.model.set(
                'name',
                this.$('.signatory-name-input').val(),
                { silent: true }
            );
        },

        setSignatoryTitle: function(event) {
            if (event && event.preventDefault) { event.preventDefault(); }
            this.model.set(
                'title',
                this.$('.signatory-title-input').val(),
                { silent: true }
            );
        },


        deleteItem: function(event) {
            if (event && event.preventDefault) { event.preventDefault(); }
            var certificate = this.model.get('certificate');
            var model = this.model;
            var self = this;

            var confirm = new PromptView.Warning({
                title: gettext('Are you sure you want to delete this signatory with title "'+model.get('title') +'"?'),
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

    console.log('certificate_editor.CertificateEditorView');
    console.log(SignatoryEditorView);
    console.log('certificate_editor.return');
    return SignatoryEditorView;
});
