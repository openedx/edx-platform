// Backbone Application View: Certificate Editor

define(['js/views/list_item_editor', 'js/certificates/models/signatory', 'js/certificates/views/signatory_editor', 'underscore', 'jquery', 'gettext'],
function(ListItemEditorView, Signatory, SignatoryEditor, _, $, gettext) {
    'use strict';
    var MIN_SIGNATORIES_LIMIT = 1;
    var MAX_SIGNATORIES_LIMIT = 4;
    var CertificateEditorView = ListItemEditorView.extend({
        tagName: 'div',
        events: {
            'change .collection-name-input': 'setName',
            'change .certificate-description-input': 'setDescription',
            'focus .input-text': 'onFocus',
            'blur .input-text': 'onBlur',
            'submit': 'setAndClose',
            'click .action-cancel': 'cancel',
            'click .action-add-signatory': 'addSignatory'
        },

        className: function () {
            // Determine the CSS class names for this model instance
            var index = this.model.collection.indexOf(this.model);

            return [
                'collection-edit',
                'certificates',
                'certificate-edit',
                'certificate-edit-' + index
            ].join(' ');
        },

        initialize: function() {
            // Set up the initial state of the attributes set for this model instance
            _.bindAll(this, "onSignatoryRemoved");
            this.eventAgg = _.extend({}, Backbone.Events);
            this.eventAgg.bind("onSignatoryRemoved", this.onSignatoryRemoved);
            ListItemEditorView.prototype.initialize.call(this);
            this.template = this.loadTemplate('certificate-editor');
        },

        onSignatoryRemoved: function(model) {
            // Event handler for model deletions
            this.model.setOriginalAttributes();
            this.render();
        },

        render: function() {
            // Assemble the editor view for this model
            ListItemEditorView.prototype.render.call(this);
            var self = this;
            // Ensure we have at least one signatory associated with the certificate.
            this.model.get("signatories").each(function( modelSignatory) {
                var signatory_view = new SignatoryEditor({
                    model: modelSignatory,
                    isEditingAllCollections: true,
                    eventAgg: self.eventAgg
                });
                self.$('div.signatory-edit-list').append($(signatory_view.render()));
            });
            this.toggleAddSignatoryButtonState();
            return this;
        },

        addSignatory: function() {
            // Append a new signatory to the certificate model's signatories collection
            var signatory = new Signatory({certificate: this.getSaveableModel()});
            this.render();
        },

        toggleAddSignatoryButtonState: function() {
            // Disable the 'Add Signatory' link if the constraint has been met.
            if(this.$(".signatory-edit-list > div.signatory-edit").length >= MAX_SIGNATORIES_LIMIT) {
                this.$(".action-add-signatory").addClass("disableClick");
            }
            else if ($(".action-add-signatory").hasClass('disableClick')) {
                this.$(".action-add-signatory").removeClass("disableClick");
            }
        },

        getTemplateOptions: function() {
            // Retrieves the current attributes/options for the model
            return {
                id: this.model.get('id'),
                uniqueId: _.uniqueId(),
                name: this.model.escape('name'),
                description: this.model.escape('description'),
                isNew: this.model.isNew()
            };
        },

        getSaveableModel: function() {
            // Returns the current model instance
            return this.model;
        },

        setName: function(event) {
            // Updates the indicated model field (still requires persistence on server)
            if (event && event.preventDefault) { event.preventDefault(); }
            this.model.set(
                'name', this.$('.collection-name-input').val(),
                { silent: true }
            );
        },

        setDescription: function(event) {
            // Updates the indicated model field (still requires persistence on server)
            if (event && event.preventDefault) { event.preventDefault(); }
            this.model.set(
                'description',
                this.$('.certificate-description-input').val(),
                { silent: true }
            );
        },

        setValues: function() {
            // Update the specified values in the local model instance
            this.setName();
            this.setDescription();
            return this;
        }
    });
    return CertificateEditorView;
});
