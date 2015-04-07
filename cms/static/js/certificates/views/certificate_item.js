// Backbone Application View: Certificate Item
// Renders an editor view or a details view depending on the state of the underlying model.

define([
    'gettext',
    'js/views/list_item',
    'js/certificates/views/certificate_details',
    'js/certificates/views/certificate_editor'
],
function (gettext, ListItemView, CertificateDetailsView, CertificateEditorView) {
    'use strict';
    var CertificateItemView = ListItemView.extend({
        events: {
            'click .delete': 'deleteItem'
        },
        tagName: 'section',
        baseClassName: 'certificate',
        canDelete: true,

        // Translators: This field pertains to the custom label for a certificate.
        itemDisplayName: gettext('certificate'),

        attributes: function () {
            // Retrieves the defined attribute set
            return {
                'id': this.model.get('id'),
                'tabindex': -1
            };
        },

        createEditView: function() {
            // Renders the editor view for this model
            return new CertificateEditorView({model: this.model});
        },

        createDetailsView: function() {
            // Renders the details view for this model
            return new CertificateDetailsView({model: this.model});
        }
    });
    return CertificateItemView;
});
