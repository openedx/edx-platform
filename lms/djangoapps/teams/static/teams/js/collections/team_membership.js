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
                    this.privileged = options.privileged;
                    this.staff = options.staff;

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

                model: TeamMembershipModel,

                canUserCreateTeam: function() {
                    // Note: non-staff and non-privileged users are automatically added to any team
                    // that they create. This means that if multiple team membership is
                    // disabled that they cannot create a new team when they already
                    // belong to one.
                    return this.privileged || this.staff || this.length === 0;
                }
            });
            return TeamMembershipCollection;
        });
}).call(this, define || RequireJS.define);
