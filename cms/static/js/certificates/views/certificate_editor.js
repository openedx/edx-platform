/**
 * This class defines an editing view for course certificates.
 * It is expected to be backed by a Certificate model.
 */
define(['js/views/list_item_editor', 'js/certificates/models/signatory', 'js/certificates/views/signatory_editor', 'underscore', 'jquery', 'gettext'],
function(ListItemEditorView, Signatory, SignatoryEditor, _, $, gettext) {
    'use strict';
    console.log('certificate_editor.start');
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

        addSignatory: function() {
            // create a new signatory
            var signatory = new Signatory({certificate: this.getSaveableModel()});
            var signatory_view = new SignatoryEditor({model: signatory});
            this.$('div.signatory-list').append($(signatory_view.render()));
            this.toggleAddSignatoryButtonState();
        },

        className: function () {
            console.log('certificate_editor.className');
            var index = this.model.collection.indexOf(this.model);

            return [
                'collection-edit',
                'certificate-edit',
                'certificate-edit-' + index
            ].join(' ');
        },

        initialize: function() {
            console.log('certificate_editor.initialize');
            ListItemEditorView.prototype.initialize.call(this);

            this.template = this.loadTemplate('certificate-editor');
        },

        render: function() {
            console.log('certificate_edit.render');
            ListItemEditorView.prototype.render.call(this);
            var self = this;

            // At-least one signatory would be associated with certificate.
            this.model.get("signatories").each(function( modelSignatory) {
                var signatory_view = new SignatoryEditor({model: modelSignatory});
                self.$('div.signatory-list').append($(signatory_view.render()));
            });

            this.toggleAddSignatoryButtonState();
            return this;
        },

        toggleAddSignatoryButtonState: function() {
            // disable the 'add signatory' link if user has added up to 4 signatories.
            if(this.$(".signatory-list > div.signatory_view").length >= MAX_SIGNATORIES_LIMIT) {
                this.$(".action-add-signatory").addClass("disableClick");
            }
            else if ($(".action-add-signatory").hasClass('disableClick')) {
                this.$(".action-add-signatory").removeClass("disableClick");
            }
        },

        getTemplateOptions: function() {
            console.log('certificate_edit.getTemplateOptions');
            return {
                id: this.model.get('id'),
                uniqueId: _.uniqueId(),
                name: this.model.escape('name'),
                description: this.model.escape('description'),
                isNew: this.model.isNew()
            };
        },

        getSaveableModel: function() {
            console.log('certificate_edit.getSaveableModel');
            return this.model;
        },

        setName: function(event) {
            console.log('certificate_edit.setName');
            if (event && event.preventDefault) { event.preventDefault(); }
            this.model.set(
                'name', this.$('.collection-name-input').val(),
                { silent: true }
            );
        },

        setDescription: function(event) {
            console.log('certificate_edit.setDescription');
            if (event && event.preventDefault) { event.preventDefault(); }
            this.model.set(
                'description',
                this.$('.certificate-description-input').val(),
                { silent: true }
            );
        },

        setValues: function() {
            console.log('certificate_edit.setValues');
            this.setName();
            this.setDescription();

            return this;
        }

    });

    console.log('certificate_editor.CertificateEditorView');
    console.log(CertificateEditorView);
    console.log('certificate_editor.return');
    return CertificateEditorView;
});
