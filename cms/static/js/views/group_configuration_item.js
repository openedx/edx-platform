define([
    'js/views/baseview', 'jquery', "gettext", 'js/views/group_configuration_details',
    'js/views/group_configuration_edit', "js/views/utils/view_utils"
], function(
    BaseView, $, gettext, GroupConfigurationDetails, GroupConfigurationEdit, ViewUtils
) {
    'use strict';
    var GroupConfigurationsItem = BaseView.extend({
        tagName: 'section',
        attributes: function () {
            return {
                'id': this.model.get('id'),
                'tabindex': -1
            };
        },
        events: {
            'click .delete': 'deleteConfiguration'
        },

        className: function () {
            var index = this.model.collection.indexOf(this.model);

            return [
                'group-configuration',
                'group-configurations-list-item',
                'group-configurations-list-item-' + index
            ].join(' ');
        },

        initialize: function() {
            this.listenTo(this.model, 'change:editing', this.render);
            this.listenTo(this.model, 'remove', this.remove);
        },

        deleteConfiguration: function(event) {
            if(event && event.preventDefault) { event.preventDefault(); }
            var self = this;
            ViewUtils.confirmThenRunOperation(
                gettext('Delete this Group Configuration?'),
                gettext('Deleting this Group Configuration is permanent and cannot be undone.'),
                gettext('Delete'),
                function() {
                    return ViewUtils.runOperationShowingMessage(
                        gettext('Deleting') + '&hellip;',
                        function () {
                            return self.model.destroy({ wait: true });
                        }
                    );
                }
            );
        },

        render: function() {
            // Removes a view from the DOM, and calls stopListening to remove
            // any bound events that the view has listened to.
            if (this.view) {
                this.view.remove();
            }

            if (this.model.get('editing')) {
                this.view = new GroupConfigurationEdit({
                    model: this.model
                });
            } else {
                this.view = new GroupConfigurationDetails({
                    model: this.model
                });
            }

            this.$el.html(this.view.render().el);

            return this;
        }
    });

    return GroupConfigurationsItem;
});
