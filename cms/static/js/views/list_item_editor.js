/**
 * A generic view to represent a list item in its editing state.
 *
 * Subclasses must implement:
 * - getTemplateOptions (function): Return an object to pass to the
 *   template.
 * - setValues (function): Set values on the model according to the
 *   DOM.
 * - getSaveableModel (function): Return the model which should be
 *   saved by this view.  Note this may be a parent model.
 */
define([
    'js/views/baseview', 'js/views/utils/view_utils', 'underscore', 'gettext'
], function(BaseView, ViewUtils, _, gettext) {
    'use strict';

    var ListItemEditorView = BaseView.extend({
        initialize: function() {
            this.listenTo(this.model, 'invalid', this.render);
            this.listenTo(this.getSaveableModel(), 'invalid', this.render);
        },

        render: function() {
            this.$el.html(this.template(_.extend({
                error: this.model.validationError || this.getSaveableModel().validationError
            }, this.getTemplateOptions())));
        },

        setAndClose: function(event) {
            if (event && event.preventDefault) { event.preventDefault(); }

            this.setValues();
            if (!this.model.isValid() || !this.getSaveableModel().isValid()) {
                return false;
            }

            ViewUtils.runOperationShowingMessage(
                gettext('Saving'),
                function () {
                    var dfd = $.Deferred();
                    var actionableModel = this.getSaveableModel();

                    actionableModel.save({}, {
                        success: function() {
                            actionableModel.setOriginalAttributes();
                            this.close();
                            dfd.resolve();
                        }.bind(this)
                    });

                    return dfd;
                }.bind(this));
        },

        cancel: function(event) {
            if (event && event.preventDefault) { event.preventDefault(); }

            this.getSaveableModel().reset();
            return this.close();
        },

        close: function() {
            this.remove();
            if (this.model.isNew() && !_.isUndefined(this.model.collection)) {
                // if the item has never been saved, remove it
                this.model.collection.remove(this.model);
            } else {
                // tell the model that it's no longer being edited
                this.model.set('editing', false);
            }

            return this;
        }
    });

    return ListItemEditorView;
});
