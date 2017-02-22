// Backbone Application View: Certificate Details

define([
    'jquery',
    'underscore',
    'underscore.string',
    'gettext',
    'js/views/baseview',
    'js/certificates/models/signatory',
    'js/certificates/views/signatory_details',
    'common/js/components/utils/view_utils',
    'jquery.smoothScroll',
    'text!templates/certificate-details.underscore'
],
function($, _, str, gettext, BaseView, SignatoryModel, SignatoryDetailsView, ViewUtils, smoothScroll,
         certificateDetailsTemplate) {
    'use strict';
    var CertificateDetailsView = BaseView.extend({
        tagName: 'div',
        events: {
            'click .edit': 'editCertificate'
        },

        className: function() {
            // Determine the CSS class names for this model instance
            return [
                'collection',
                'certificates',
                'certificate-details'
            ].join(' ');
        },

        initialize: function() {
            // Set up the initial state of the attributes set for this model instance
            this.showDetails = true;
            this.listenTo(this.model, 'change', this.render);
        },

        editCertificate: function(event) {
            // Flip the model into 'editing' mode
            if (event && event.preventDefault) { event.preventDefault(); }
            var self = this;
            if (this.model.get('is_active') === true) {
                ViewUtils.confirmThenRunOperation(
                    gettext('Edit this certificate?'),
                    gettext('This certificate has already been activated and is live. Are you sure you want to continue editing?'),
                    gettext('Yes, allow edits to the active Certificate'),
                    function() {
                        return self.model.set('editing', true);
                    }
                );
            }
            else {
                this.model.set('editing', true);
            }
        },

        render: function(showDetails) {
            // Assemble the details view for this model
            // Expand to show all model data, if requested
            var attrs = $.extend({}, this.model.attributes, {
                index: this.model.collection.indexOf(this.model),
                showDetails: this.showDetails || showDetails || false
            });
            this.$el.html(_.template(certificateDetailsTemplate)(attrs));
            if (this.showDetails || showDetails) {
                var self = this;
                this.model.get('signatories').each(function(modelSignatory) {
                    var signatory_detail_view = new SignatoryDetailsView({model: modelSignatory});
                    self.$('div.signatory-details-list').append($(signatory_detail_view.render().$el));
                });
            }

            if (this.model.collection.length > 0 && window.certWebPreview) {
                window.certWebPreview.show();
            }
            $.smoothScroll({
                offset: 0,
                easing: 'swing',
                speed: 1000
            });
            return this;
        }
    });
    return CertificateDetailsView;
});
