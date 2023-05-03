/**
 * This class defines a details view for content experiment group configurations.
 * It is expected to be instantiated with a GroupConfiguration model.
 */
define([
    'js/views/baseview', 'underscore', 'gettext', 'underscore.string',
    'edx-ui-toolkit/js/utils/string-utils', 'edx-ui-toolkit/js/utils/html-utils'
],
function(BaseView, _, gettext, str, StringUtils, HtmlUtils) {
    'use strict';
    var GroupConfigurationDetailsView = BaseView.extend({
        tagName: 'div',
        events: {
            'click .edit': 'editConfiguration',
            'click .show-groups': 'showGroups',
            'click .hide-groups': 'hideGroups'
        },

        className: function() {
            var index = this.model.collection.indexOf(this.model);

            return [
                'collection',
                'group-configuration-details',
                'group-configuration-details-' + index
            ].join(' ');
        },

        initialize: function() {
            this.template = HtmlUtils.template(
                $('#group-configuration-details-tpl').text()
            );
            this.listenTo(this.model, 'change', this.render);
        },

        render: function() {
            var attrs = $.extend({}, this.model.attributes, {
                groupsCountMessage: this.getGroupsCountTitle(),
                usageCountMessage: this.getUsageCountTitle(),
                courseOutlineUrl: this.model.collection.outlineUrl,
                index: this.model.collection.indexOf(this.model)
            });
            HtmlUtils.setHtml(this.$el, this.template(attrs));
            return this;
        },

        editConfiguration: function(event) {
            if (event && event.preventDefault) { event.preventDefault(); }
            this.model.set('editing', true);
        },

        showGroups: function(event) {
            if (event && event.preventDefault) { event.preventDefault(); }
            this.model.set('showGroups', true);
        },

        hideGroups: function(event) {
            if (event && event.preventDefault) { event.preventDefault(); }
            this.model.set('showGroups', false);
        },

        getGroupsCountTitle: function() {
            var count = this.model.get('groups').length,
                /* globals ngettext */
                message = ngettext(
                    /*
                        Translators: 'count' is number of groups that the group
                        configuration contains.
                    */
                    'Contains {count} group', 'Contains {count} groups',
                    count
                );

            return StringUtils.interpolate(message, {count: count});
        },

        getUsageCountTitle: function() {
            var count = this.model.get('usage').length;

            if (count === 0) {
                return gettext('Not in Use');
            } else {
                return StringUtils.interpolate(ngettext(

                    /*
                        Translators: 'count' is number of units that the group
                        configuration is used in.
                    */
                    'Used in {count} location', 'Used in {count} locations',
                    count
                ),
                {count: count}
                );
            }
        }
    });

    return GroupConfigurationDetailsView;
});
