/**
 * This class defines an editing view for course certificates.
 * It is expected to be backed by a Certificate model.
 */
define(['js/views/list_item_editor', 'underscore', 'jquery', 'gettext'],
function(ListItemEditorView, _, $, gettext) {
    'use strict';
    console.log('certificate_editor.start');
    var CertificateEditorView = ListItemEditorView.extend({
        tagName: 'div',
        events: {
            'change .collection-name-input': 'setName',
            'change .certificate-description-input': 'setDescription',
            'focus .input-text': 'onFocus',
            'blur .input-text': 'onBlur',
            'submit': 'setAndClose',
            'click .action-cancel': 'cancel'
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
            return this;
        },

        getTemplateOptions: function() {
            console.log('certificate_edit.getTemplateOptions');
            return {
                id: this.model.get('id'),
                uniqueId: _.uniqueId(),
                name: this.model.escape('name'),
                description: this.model.escape('description'),
                isNew: this.model.isNew(),
                signatories: this.model.get('signatories')
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

        setSignatoryAttributes: function() {
            //initialize the signatory model and set the corresponding attributes.
            //TODO: we need to make this approach dynamic for signatory collections. e.g. 1 to 4 signatories.
            //TODO: currently assuming only one signatory in certificate.
            var signatory = this.model.get('signatories').first();
            signatory.set('name', this.$('.signatory-name-input').val(), { silent: true });
            signatory.set('title', this.$('.signatory-title-input').val(), { silent: true });
            //signatory.set('certificate', this.model , { silent: true });
            return signatory;
        },

        setValues: function() {
            console.log('certificate_edit.setValues');
            this.setName();
            this.setDescription();
            this.setSignatoryAttributes();
            return this;
        }

    });

    console.log('certificate_editor.CertificateEditorView');
    console.log(CertificateEditorView);
    console.log('certificate_editor.return');
    return CertificateEditorView;
});
