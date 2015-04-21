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
