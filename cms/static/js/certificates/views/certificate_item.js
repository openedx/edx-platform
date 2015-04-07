/**
 * This class defines an controller view for certificates.
 * It renders an editor view or a details view depending on the state
 * of the underlying model.
 * It is expected to be backed by a Certificate model.
 */
define([
    'js/views/list_item', 'js/certificates/views/certificate_details', 'js/certificates/views/certificate_editor', 'gettext'
], function(
    ListItemView, CertificateDetailsView, CertificateEditorView, gettext
) {
    'use strict';
    console.log('certificate_item.start')
    var CertificateItemView = ListItemView.extend({
        events: {
            'click .delete': 'deleteItem'
        },

        tagName: 'section',

        baseClassName: 'certificate',

        canDelete: true,

        // Translators: this refers to a certificate.
        itemDisplayName: gettext('certificate'),

        attributes: function () {
            return {
                'id': this.model.get('id'),
                'tabindex': -1
            };
        },

        createEditView: function() {
            console.log('certificate_item.createEditView');
            return new CertificateEditorView({model: this.model});
        },

        createDetailsView: function() {
            console.log('certificate_item.createDetailsView');
            return new CertificateDetailsView({model: this.model});
        }
    });
    console.log('certificate_item.CertificateItemView');
    console.log(CertificateItemView);
    console.log('certificate_item.return');
    return CertificateItemView;
});
