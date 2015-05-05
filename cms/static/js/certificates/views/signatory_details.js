/**
 * This class defines a details view for signatories of certificate.
 */
define([
    'js/views/baseview', 'js/views/utils/view_utils', 'js/certificates/views/signatory_editor', 'underscore', "js/utils/templates", 'gettext', 'underscore.string'
],
function(BaseView, ViewUtils, SignatoryEditorView, _, TemplateUtils, gettext, str) {
    'use strict';
    console.log('signatory_details.start');
    var SignatoryDetailsView = BaseView.extend({
        tagName: 'div',
        events: {
            'click .edit-signatory': 'editSignatory',
            'click  .signatory-panel-save': 'saveSignatoryData',
            'click  .signatory-panel-close': 'closeSignatoryEditView'

        },

        className: function () {
            console.log('signatory_details.className');
            var index = this.model.collection.indexOf(this.model);

            return [
                'signatory-details',
                'signatory-details-view-' + index
            ].join(' ');
        },

        initialize: function() {
            console.log('signatory_details.initialize');
            this.template = this.loadTemplate('signatory-details');
            this.listenTo(this.model, 'change', this.render);
        },

        loadTemplate: function(name) {
            return TemplateUtils.loadTemplate(name);
        },

        editSignatory: function(event) {
            console.log('signatory_details.editSignatory');
            if (event && event.preventDefault) { event.preventDefault(); }
            var view =  new SignatoryEditorView({model: this.model, isEditingAllCollections: false});
            this.$el.html(view.render());
        },

        saveSignatoryData: function(event) {
            if (event && event.preventDefault) { event.preventDefault(); }

            // relational model contains the reverse relation to parent.
            // getting certificate object here.
            var certificate = this.model.get('certificate');
            var self = this;

            ViewUtils.runOperationShowingMessage(
                gettext('Saving'),
                function () {
                    var dfd = $.Deferred();
                    var actionableModel = certificate;
                    actionableModel.save({}, {
                        success: function() {
                            actionableModel.setOriginalAttributes();
                            dfd.resolve();
                            self.closeSignatoryEditView();
                        }.bind(this)
                    });

                    return dfd;
                }.bind(this));

        },

        closeSignatoryEditView: function(event) {
            if (event && event.preventDefault) { event.preventDefault(); }
            this.render();
        },

        render: function() {
            console.log('signatory_details.render');
            var attributes = $.extend({}, this.model.attributes, {
                signatory_number: this.model.collection.indexOf(this.model) + 1
            });

            return $(this.el).html(this.template(attributes));
        }

    });

    console.log('signatory_details.SignatoryDetailsView');
    console.log(SignatoryDetailsView);
    console.log('signatory_details.return');
    return SignatoryDetailsView;
});
