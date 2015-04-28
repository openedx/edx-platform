/**
 * This class defines an editing view for course certificates.
 * It is expected to be backed by a Certificate model.
 */
define(['js/views/list_item_editor', 'js/certificates/models/signatory' ,"js/utils/templates", 'underscore', 'jquery', 'gettext'],
function(ListItemEditorView, Signatory, TemplateUtils, _, $, gettext) {
    'use strict';
    console.log('certificate_editor.start');
    var SignatoryEditorView = Backbone.View.extend({
        tagName: 'div',
        className: 'signatory_view signatory-edit',
        events: {
            'change .signatory-name-input': 'setSignatoryName',
            'change .signatory-title-input': 'setSignatoryTitle'
        },

        initialize: function() {
             _.bindAll(this, 'render');
            this.model.bind('change', this.render);
            this.template = this.loadTemplate('signatory-editor');
        },

        loadTemplate: function(name) {
            return TemplateUtils.loadTemplate(name);
        },

        render: function() {
            var data = this.model.toJSON();
            var index = this.model.collection.indexOf(this.model) + 1;
            data['signatory_number'] = index;
            return $(this.el).html(this.template(data));
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
