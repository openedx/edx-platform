(function(define) {
    'use strict';

    define(['underscore', 'backbone', 'gettext', 'teams/js/views/teams', 'edx-ui-toolkit/js/utils/html-utils'],
        function(_, Backbone, gettext, TeamsView, HtmlUtils) {
            var MyTeamsView = TeamsView.extend({

                initialize: function(options) {
                    this.getTopic = options.getTopic;
                    TeamsView.prototype.initialize.call(this, options);
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

                getTopicType: function(topicId) {
                    var deferred = $.Deferred();
                    this.getTopic(topicId).done(function(topic) {
                        deferred.resolve(topic.get('type'));
                    });
                    return deferred.promise();
                },

                createHeaderView: function() {
                    // Never show a pagination header for the "My Team" tab
                    // because there is only ever one team.
                    return null;
                },

                createFooterView: function() {
                    // Never show a pagination footer for the "My Team" tab
                    // because there is only ever one team.
                    return null;
                }
            });

            return MyTeamsView;
        });
}).call(this, define || RequireJS.define);
