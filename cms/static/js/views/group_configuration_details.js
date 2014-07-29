define([
    'js/views/baseview', 'underscore', 'gettext', 'underscore.string'
],
function(BaseView, _, gettext, str) {
    'use strict';
    var GroupConfigurationDetails = BaseView.extend({
        tagName: 'div',
        events: {
            'click .edit': 'editConfiguration',
            'click .show-groups': 'showGroups',
            'click .hide-groups': 'hideGroups'
        },

        className: function () {
            var index = this.model.collection.indexOf(this.model);

            return [
                'group-configuration-details',
                'group-configuration-details-' + index
            ].join(' ');
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
                usageCountMessage: this.getUsageCountTitle(),
                outlineAnchorMessage: this.getOutlineAnchorMessage(),
                index: this.model.collection.indexOf(this.model)
            });

            this.$el.html(this.template(attrs));
            return this;
        },

        editConfiguration: function(event) {
            if(event && event.preventDefault) { event.preventDefault(); }
            this.model.set('editing', true);
        },

        showGroups: function(event) {
            if(event && event.preventDefault) { event.preventDefault(); }
            this.model.set('showGroups', true);
        },

        hideGroups: function(event) {
            if(event && event.preventDefault) { event.preventDefault(); }
            this.model.set('showGroups', false);
        },

        getGroupsCountTitle: function () {
            var count = this.model.get('groups').length,
                message = ngettext(
                    /*
                        Translators: 'count' is number of groups that the group
                        configuration contains.
                    */
                    'Contains %(count)s group', 'Contains %(count)s groups',
                    count
                );

            return interpolate(message, { count: count }, true);
        },

        getUsageCountTitle: function () {
            var count = this.model.get('usage').length, message;

            if (count === 0) {
                message = gettext('Not in Use');
            } else {
                message = ngettext(
                    /*
                        Translators: 'count' is number of units that the group
                        configuration is used in.
                    */
                    'Used in %(count)s unit', 'Used in %(count)s units',
                    count
                );
            }

            return interpolate(message, { count: count }, true);
        },

        getOutlineAnchorMessage: function () {
            var message = gettext(
                    /*
                        Translators: 'outlineAnchor' is an anchor pointing to
                        the course outline page.
                    */
                    'This Group Configuration is not in use. Start by adding a content experiment to any Unit via the %(outlineAnchor)s.'
                ),
                anchor = str.sprintf(
                    '<a href="%(url)s" title="%(text)s">%(text)s</a>',
                    {
                            url: this.model.collection.outlineUrl,
                            text: gettext('Course Outline')
                    }
                );

            return str.sprintf(message, {outlineAnchor: anchor});
        }
    });

    return GroupConfigurationDetails;
});
