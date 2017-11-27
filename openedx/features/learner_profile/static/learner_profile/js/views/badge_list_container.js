(function(define) {
    'use strict';

    define(
        [
            'gettext', 'common/js/components/views/paginated_view',
            'learner_profile/js/views/badge_view', 'learner_profile/js/views/badge_list_view',
            'text!learner_profile/templates/badge_list.underscore'
        ],
        function(gettext, PaginatedView, BadgeView, BadgeListView, BadgeListTemplate) {
            var BadgeListContainer = PaginatedView.extend({
                type: 'badge',

                itemViewClass: BadgeView,

                listViewClass: BadgeListView,

                viewTemplate: BadgeListTemplate,

                isZeroIndexed: true,

                paginationLabel: gettext('Accomplishments Pagination'),

                initialize: function(options) {
                    BadgeListContainer.__super__.initialize.call(this, options);
                    this.listView.find_courses_url = options.find_courses_url;
                    this.listView.badgeMeta = options.badgeMeta;
                    this.listView.ownProfile = options.ownProfile;
                }
            });

            return BadgeListContainer;
        });
}).call(this, define || RequireJS.define);
