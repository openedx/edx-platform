/**
 * This class defines a simple display view for a partition group.
 * It is expected to be backed by a Group model.
 */
define([
    'js/views/baseview', 'underscore', 'gettext', 'underscore.string',
    'edx-ui-toolkit/js/utils/string-utils', 'edx-ui-toolkit/js/utils/html-utils'
], function(BaseView, _, gettext, str, StringUtils, HtmlUtils) {
    'use strict';

    var PartitionGroupDetailsView = BaseView.extend({
        tagName: 'div',
        events: {
            'click .edit': 'editGroup',
            'click .show-groups': 'showContentGroupUsages',
            'click .hide-groups': 'hideContentGroupUsages'
        },

        className: function() {
            var index = this.model.collection.indexOf(this.model);

            return [
                'collection',
                'partition-group-details',
                'partition-group-details-' + index
            ].join(' ');
        },

        editGroup: function() {
            this.model.set({editing: true});
        },

        initialize: function() {
            this.template = this.loadTemplate('partition-group-details');
            this.restrictEditing = this.options.restrictEditing || false;
            this.listenTo(this.model, 'change', this.render);
        },

        render: function(showContentGroupUsages) {
            var attrs = $.extend({}, this.model.attributes, {
                usageCountMessage: this.getUsageCountTitle(),
                courseOutlineUrl: this.model.collection.parents[0].outlineUrl,
                index: this.model.collection.indexOf(this.model),
                showContentGroupUsages: showContentGroupUsages || false,
                HtmlUtils: HtmlUtils,
                restrictEditing: this.restrictEditing
            });
            HtmlUtils.setHtml(this.$el, HtmlUtils.HTML(this.template(attrs)));
            return this;
        },

        showContentGroupUsages: function(event) {
            if (event && event.preventDefault) { event.preventDefault(); }
            this.render(true);
        },

        hideContentGroupUsages: function(event) {
            if (event && event.preventDefault) { event.preventDefault(); }
            this.render(false);
        },

        getUsageCountTitle: function() {
            var count = this.model.get('usage').length;

            if (count === 0) {
                return gettext('Not in Use');
            } else {
                /* globals ngettext */
                return StringUtils.interpolate(ngettext(
                    /*
                        Translators: 'count' is number of locations that the group
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

    return PartitionGroupDetailsView;
});
