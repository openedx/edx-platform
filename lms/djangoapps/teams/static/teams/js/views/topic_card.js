/**
 * View for a topic card. Displays a Topic.
 */
;(function(define) {
    'use strict';
    define([
            'backbone', 'underscore', 'gettext', 'js/components/card/views/card',
            'edx-ui-toolkit/js/utils/html-utils'
        ],
        function(Backbone, _, gettext, CardView, HtmlUtils) {
            var TeamCountDetailView = Backbone.View.extend({
                tagName: 'p',
                className: 'team-count',

                initialize: function() {
                    this.render();
                },

                render: function() {
                    var teamCount = this.model.get('team_count');
                    this.$el.html(HtmlUtils.interpolateHtml(
                        ngettext('{team_count} Team', '{team_count} Teams', teamCount),
                        {team_count: teamCount}
                    ).toString());
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
                actionContent: function() {
                    var screenReaderText = HtmlUtils.interpolateHtml(
                        gettext('View Teams in the {topic_name} Topic'),
                        {topic_name: this.model.get('name')}
                    );
                    return HtmlUtils.HTML(
                        '<span class="sr">' +
                        screenReaderText +
                        '</span><i class="icon fa fa-arrow-right" aria-hidden="true"></i>'
                    );
                }
            });

            return TopicCardView;
        });
}).call(this, define || RequireJS.define);
