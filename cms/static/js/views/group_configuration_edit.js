define([
    'js/views/baseview', 'underscore', 'jquery', 'gettext', 'js/views/utils/view_utils'
],
function(BaseView, _, $, gettext, ViewUtils) {
    'use strict';
    var GroupConfigurationEdit = BaseView.extend({
        tagName: 'div',
        events: {
            'change .group-configuration-name-input': 'setName',
            'change .group-configuration-description-input': 'setDescription',
            'focus .input-text': 'onFocus',
            'blur .input-text': 'onBlur',
            'submit': 'setAndClose',
            'click .action-cancel': 'cancel'
        },

        className: function () {
            var index = this.model.collection.indexOf(this.model);

            return [
                'group-configuration-edit',
                'group-configuration-edit-' + index
            ].join(' ');
        },

        initialize: function() {
            this.template = this.loadTemplate('group-configuration-edit');
            this.listenTo(this.model, 'invalid', this.render);
        },

        render: function() {
            this.$el.html(this.template({
                id: this.model.get('id'),
                uniqueId: _.uniqueId(),
                name: this.model.escape('name'),
                description: this.model.escape('description'),
                isNew: this.model.isNew(),
                error: this.model.validationError
            }));

            return this;
        },

        setName: function(event) {
            if(event && event.preventDefault) { event.preventDefault(); }
            this.model.set(
                'name', this.$('.group-configuration-name-input').val(),
                { silent: true }
            );
        },

        setDescription: function(event) {
            if(event && event.preventDefault) { event.preventDefault(); }
            this.model.set(
                'description',
                this.$('.group-configuration-description-input').val(),
                { silent: true }
            );
        },

        setValues: function() {
            this.setName();
            this.setDescription();

            return this;
        },

        setAndClose: function(event) {
            if(event && event.preventDefault) { event.preventDefault(); }

            this.setValues();
            if(!this.model.isValid()) {
                return false;
            }

            ViewUtils.runOperationShowingMessage(
                gettext('Saving') + '&hellip;',
                function () {
                    var dfd = $.Deferred();

                    this.model.save({}, {
                        success: function() {
                            this.model.setOriginalAttributes();
                            this.close();
                            dfd.resolve();
                        }.bind(this)
                    });

                    return dfd;
                }.bind(this)
            );
        },

        cancel: function(event) {
            if(event && event.preventDefault) { event.preventDefault(); }

            this.model.reset();
            return this.close();
        },

        close: function() {
            var groupConfigurations = this.model.collection;

            this.remove();
            if(this.model.isNew()) {
                // if the group configuration has never been saved, remove it
                groupConfigurations.remove(this.model);
            } else {
                // tell the model that it's no longer being edited
                this.model.set('editing', false);
            }

            return this;
        }
    });

    return GroupConfigurationEdit;
});
