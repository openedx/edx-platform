;(function (define) {
    'use strict';

    define(['backbone', 'gettext', 'teams/js/views/teams'],
        function (Backbone, gettext, TeamsView) {
            var MyTeamsView = TeamsView.extend({
                className: 'my-teams',

                initialize: function(options) {
                    TeamsView.prototype.initialize.call(this, options);
                    this.allowMultipleTeamMembership = options.allowMultipleTeamMembership;
                },

                render: function() {
                    TeamsView.prototype.render.call(this);
                    if (this.collection.length === 0) {
                        this.$el.append('<p>' + gettext('You are not currently a member of any teams.') + '</p>');
                    }
                    return this;
                },

                createHeaderView: function() {
                    if (this.allowMultipleTeamMembership) {
                        return TeamsView.prototype.createHeaderView.call(this);
                    }
                    return null;
                },

                createFooterView: function() {
                    if (this.allowMultipleTeamMembership) {
                        return TeamsView.prototype.createFooterView.call(this);
                    }
                    return null;
                }
            });

            return MyTeamsView;
        });
}).call(this, define || RequireJS.define);
