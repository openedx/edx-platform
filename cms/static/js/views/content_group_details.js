/**
 * This class defines a simple display view for a content group.
 * It is expected to be backed by a Group model.
 */
define([
    'js/views/baseview'
], function(BaseView) {
    'use strict';

    var ContentGroupDetailsView = BaseView.extend({
        tagName: 'div',
        className: 'content-group-details collection',

        events: {
            'click .edit': 'editGroup'
        },

        editGroup: function() {
            this.model.set({'editing': true});
        },

        initialize: function() {
            this.template = this.loadTemplate('content-group-details');
        },

        render: function() {
            this.$el.html(this.template(this.model.toJSON()));
        }
    });

    return ContentGroupDetailsView;
});
