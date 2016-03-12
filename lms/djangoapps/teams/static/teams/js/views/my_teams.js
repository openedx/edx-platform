(function(define) {
    'use strict';

    define(['backbone', 'gettext',
            'edx-ui-toolkit/js/utils/html-utils',
            'teams/js/views/teams'],
        function(Backbone, gettext, HtmlUtils, TeamsView) {
            var MyTeamsView = TeamsView.extend({
                render: function() {
                    var view = this;
                    if (this.collection.isStale) {
                        HtmlUtils.setHtml(this.$el, '');
                    }
                    this.collection.refresh()
                        .done(function() {
                            TeamsView.prototype.render.call(view);
                            if (view.collection.length === 0) {
                                HtmlUtils.append(
                                    view.$el,
                                    HtmlUtils.joinHtml(
                                        HtmlUtils.HTML('<p>'),
                                        gettext('You are not currently a member of any team.'),
                                        HtmlUtils.HTML('</p>')
                                    )
                                );
                            }
                        });
                    return this;
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
