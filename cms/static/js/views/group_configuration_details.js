define([
    'js/views/baseview', 'underscore', 'gettext'
],
function(BaseView, _, gettext) {
    'use strict';
    var GroupConfigurationDetails = BaseView.extend({
        tagName: 'section',
        className: 'group-configuration',
        events: {
            'click .show-groups': 'showGroups',
            'click .hide-groups': 'hideGroups'
        },

        initialize: function() {
            this.template = _.template(
                $('#group-configuration-details-tpl').text()
            );
            this.listenTo(this.model, 'change', this.render);
        },

        render: function() {
            var attrs = $.extend({}, this.model.attributes, {
                groupsCountMessage: this.getGroupsCountTitle(),
                index: this.model.collection.indexOf(this.model)
            });

            this.$el.html(this.template(attrs));
            return this;
        },

        showGroups: function(e) {
            if(e && e.preventDefault) { e.preventDefault(); }
            this.model.set('showGroups', true);
        },

        hideGroups: function(e) {
            if(e && e.preventDefault) { e.preventDefault(); }
            this.model.set('showGroups', false);
        },

        getGroupsCountTitle: function () {
            var count = this.model.get('groups').length,
                message = ngettext(
                    // Translators: 'count' is number of groups that the group configuration contains.
                    'Contains %(count)s group', 'Contains %(count)s groups',
                    count
                );

            return interpolate(message, { count: count }, true);
        }
    });

    return GroupConfigurationDetails;
});
