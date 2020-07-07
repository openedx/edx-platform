(function(define) {
    'use strict';

    define(['underscore', 'backbone', 'gettext', 'teams/js/views/teams', 'edx-ui-toolkit/js/utils/html-utils'],
        function(_, Backbone, gettext, TeamsView, HtmlUtils) {
            var MyTeamsView = TeamsView.extend({

                initialize: function(options) {
                    this.getTopic = options.getTopic;
                    TeamsView.prototype.initialize.call(
                        this,
                        _.extend(
                            { showTeamset: true },
                            options
                        )
                    );
                },

                render: function() {
                    var view = this;
                    if (this.collection.isStale) {
                        this.$el.html('');
                    }
                    this.collection.refresh()
                        .done(function() {
                            TeamsView.prototype.render.call(view);
                            if (view.collection.length === 0) {
                                HtmlUtils.append(view.$el, gettext('You are not currently a member of any team.'));
                            }
                        });
                    return this;
                },

                getTopic: function(topicId) {
                    return this.getTopic(topicId);
                },

                createHeaderView: function() {
                    // hide pagination when learner isn't a member of any teams
                    if (!this.collection.length) {
                        return null;
                    } else {
                        return TeamsView.prototype.createHeaderView.call(this);
                    }
                },

                createFooterView: function() {
                    // hide pagination when learner isn't a member of any teams
                    if (!this.collection.length) {
                        return null;
                    } else {
                        return TeamsView.prototype.createFooterView.call(this);
                    }
                }
            });

            return MyTeamsView;
        });
}).call(this, define || RequireJS.define);
