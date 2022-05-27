/**
 * This class defines a list view for partition groups.
 * It is expected to be backed by a Group collection.
 */
define([
    'underscore', 'js/views/list', 'js/views/partition_group_item', 'gettext'
], function(_, ListView, PartitionGroupItemView, gettext) {
    'use strict';

    var PartitionGroupListView = ListView.extend({
        initialize: function(options) {
            ListView.prototype.initialize.apply(this, [options]);
            this.scheme = options.scheme;
        },

        tagName: 'div',

        className: 'partition-group-list',

        // Translators: This refers to a content group that can be linked to a student cohort.
        itemCategoryDisplayName: gettext('content group'),

        newItemMessage: gettext('Add your first content group'),

        emptyMessage: gettext('You have not created any content groups yet.'),

        createItemView: function(options) {
            return new PartitionGroupItemView(_.extend({}, options, {scheme: this.scheme}));
        }
    });

    return PartitionGroupListView;
});
