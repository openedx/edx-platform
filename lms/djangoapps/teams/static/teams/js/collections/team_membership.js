;(function (define) {
    'use strict';
    define(['teams/js/collections/base', 'teams/js/models/team_membership'],
        function(BaseCollection, TeamMembershipModel) {
            var TeamMembershipCollection = BaseCollection.extend({
                initialize: function(team_memberships, options) {
                    var self = this;
                    BaseCollection.prototype.initialize.call(this, options);

                    this.perPage = options.per_page || 10;
                    this.username = options.username;

                    this.server_api = _.extend(
                        {
                            expand: 'team,user',
                            username: this.username,
                            course_id: function () { return encodeURIComponent(self.course_id); }
                        },
                        BaseCollection.prototype.server_api
                    );
                    delete this.server_api['sort_order']; // Sort order is not specified for the TeamMembership API
                    delete this.server_api['order_by']; // Order by is not specified for the TeamMembership API
                },

                model: TeamMembershipModel
            });
            return TeamMembershipCollection;
        });
}).call(this, define || RequireJS.define);
