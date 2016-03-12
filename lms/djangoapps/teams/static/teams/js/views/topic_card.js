/**
 * View for a topic card. Displays a Topic.
 */
(function(define) {
    'use strict';
    define(
        [
            'underscore',
            'backbone',
            'gettext',
            'edx-ui-toolkit/js/utils/html-utils',
            'edx-ui-toolkit/js/utils/string-utils',
            'js/components/card/views/card'
        ],
        function(_, Backbone, gettext, HtmlUtils, StringUtils, CardView) {
            var TeamCountDetailView = Backbone.View.extend({
                tagName: 'p',
                className: 'team-count',

                initialize: function() {
                    this.render();
                },

                render: function() {
                    var teamCount = this.model.get('team_count');
                    this.$el.text(
                        StringUtils.interpolate(
                            ngettext('{team_count} Team', '{team_count} Teams', teamCount),
                            {team_count: teamCount}
                        )
                    );
                    return this;
                }
            });

            var TopicCardView = CardView.extend({
                initialize: function() {
                    this.detailViews = [new TeamCountDetailView({model: this.model})];
                    CardView.prototype.initialize.apply(this, arguments);
                },

                actionUrl: function() {
                    return '#topics/' + this.model.get('id');
                },

                configuration: 'square_card',
                cardClass: 'topic-card',
                pennant: gettext('Topic'),
                title: function() { return this.model.get('name'); },
                description: function() { return this.model.get('description'); },
                details: function() { return this.detailViews; },
                actionClass: 'action-view',
                actionContentHtml: function() {
                    return HtmlUtils.joinHtml(
                        HtmlUtils.HTML('<span class="sr">'),
                        StringUtils.interpolate(
                            gettext('View Teams in the {topic_name} Topic'),
                            {topic_name: this.model.get('name')}
                        ),
                        HtmlUtils.HTML('</span>'),
                        HtmlUtils.HTML('<span class="icon fa fa-arrow-right" aria-hidden="true"></span>')
                    );
                }
            });

            return TopicCardView;
        });
}).call(this, define || RequireJS.define);
