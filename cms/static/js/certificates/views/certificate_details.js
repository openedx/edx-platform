// Backbone Application View: Certificate Details

define([
    'jquery',
    'underscore',
    'underscore.string',
    'gettext',
    'js/views/baseview',
    'js/certificates/models/signatory',
    'js/certificates/views/signatory_details',
    'js/views/utils/view_utils'
],
function($, _, str, gettext, BaseView, SignatoryModel, SignatoryDetailsView, ViewUtils) {
    'use strict';
    var CertificateDetailsView = BaseView.extend({
        tagName: 'div',
        events: {
            'click .edit': 'editCertificate',
            'click .show-details': 'showDetails',
            'click .hide-details': 'hideDetails',
            'click .activate-cert, .deactivate-cert': "handleCertificateActivation"
        },

        className: function () {
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
            this.template = this.loadTemplate('certificate-details');
            //this.listenTo(this.model, 'change', this.render);
        },

        handleCertificateActivation: function(event) {
            var msg = null;
            switch (event.currentTarget.id) {
                case 'activate-certificate':
                    this.model.set('is_active', true);
                    msg = 'Activating';
                    break;
                case 'deactivate-certificate':
                    this.model.set('is_active', false);
                    msg = 'Deactivating';
                    break;
                default:
                    break;
            }

            if(msg) {
                ViewUtils.runOperationShowingMessage(
                    gettext(msg),
                    function () {
                        var dfd = $.Deferred();
                        var actionableModel = this.model;
                        actionableModel.save({wait:true}, {
                            success: function () {
                                actionableModel.setOriginalAttributes();
                                $("button.activate-cert").toggleClass("active-state de-active-state");
                                $("button.deactivate-cert").toggleClass("active-state de-active-state");
                                dfd.resolve();
                            }.bind(this)
                        });
                        return dfd;
                    }.bind(this));
            }
        },

        editCertificate: function(event) {
            // Flip the model into 'editing' mode
            if (event && event.preventDefault) { event.preventDefault(); }
            this.model.set('editing', true);
        },

        showDetails: function(event) {
            // Expand the detail view for this item/model
            if (event && event.preventDefault) { event.preventDefault(); }
            this.render(true);
        },

        hideDetails: function(event) {
            // Collapse the detail view for this item/model
            if (event && event.preventDefault) { event.preventDefault(); }
            this.render(false);
        },

        render: function(showDetails) {
            // Assemble the details view for this model
            // Expand to show all model data, if requested
            var attrs = $.extend({}, this.model.attributes, {
                index: this.model.collection.indexOf(this.model),
                showDetails: this.showDetails || showDetails || false
            });
            this.$el.html(this.template(attrs));
            if(this.showDetails || showDetails) {
                var self = this;
                this.model.get("signatories").each(function (modelSignatory) {
                    var signatory_detail_view = new SignatoryDetailsView({model: modelSignatory});
                    self.$('div.signatory-details-list').append($(signatory_detail_view.render().$el));
                });
            }

            if(this.model.collection.length > 0 && window.certWebPreview) {
                window.certWebPreview.show();
            }

            return this;
        }
    });
    return CertificateDetailsView;
});
