;(function (define, undefined) {
    'use strict';
    define([
        'gettext', 'jquery', 'underscore', 'common/js/components/views/paginated_view',
        'js/student_profile/views/badge_view', 'js/student_profile/views/badge_list_view',
        'text!templates/student_profile/badge_list.underscore'],
        function (gettext, $, _, PaginatedView, BadgeView, BadgeListView, BadgeListTemplate) {
            var BadgeListContainer = PaginatedView.extend({
                type: 'badge',

                itemViewClass: BadgeView,

                listViewClass: BadgeListView,

                viewTemplate: BadgeListTemplate,

                isZeroIndexed: true,

                paginationLabel: gettext('Accomplishments Pagination'),

                initialize: function (options) {
                    BadgeListContainer.__super__.initialize.call(this, options);
                    this.listView.find_courses_url = options.find_courses_url;
                    this.listView.badgeMeta = options.badgeMeta;
                    this.listView.ownProfile = options.ownProfile;
                }
            });

            return BadgeListContainer;
        });
}).call(this, define || RequireJS.define);
