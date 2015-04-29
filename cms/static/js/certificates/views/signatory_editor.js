/**
 * This class defines an editing view for course certificates.
 * It is expected to be backed by a Certificate model.
 */
define(['js/views/list_item_editor', 'js/utils/templates', 'underscore', 'jquery', 'gettext'],
function(ListItemEditorView, TemplateUtils, _, $, gettext) {
    'use strict';
    console.log('certificate_editor.start');
    var SignatoryEditorView = Backbone.View.extend({
        tagName: 'div',
        events: {
            'change .signatory-name-input': 'setSignatoryName',
            'change .signatory-title-input': 'setSignatoryTitle'
        },

        className: function () {
            console.log('signatory_editor.className');
            var index = this.model.collection.indexOf(this.model);

            return [
                'signatory-edit',
                'signatory-edit-view-' + index
            ].join(' ');
        },

        initialize: function(options) {
             _.bindAll(this, 'render');
            this.model.bind('change', this.render);
            this.isEditingAllCollections = options.isEditingAllCollections;
            this.template = this.loadTemplate('signatory-editor');
        },

        loadTemplate: function(name) {
            return TemplateUtils.loadTemplate(name);
        },

        render: function() {
            var attributes = $.extend({
                isEditingAllCollections: this.isEditingAllCollections}, this.model.attributes, {
                signatory_number: this.model.collection.indexOf(this.model) + 1
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
        }
    });

    console.log('certificate_editor.CertificateEditorView');
    console.log(SignatoryEditorView);
    console.log('certificate_editor.return');
    return SignatoryEditorView;
});
