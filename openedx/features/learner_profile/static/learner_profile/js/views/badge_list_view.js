(function(define) {
    'use strict';

    define([
        'gettext',
        'jquery',
        'underscore',
        'edx-ui-toolkit/js/utils/html-utils',
        'common/js/components/views/list',
        'learner_profile/js/views/badge_view',
        'text!learner_profile/templates/badge_placeholder.underscore'
    ],
        function(gettext, $, _, HtmlUtils, ListView, BadgeView, badgePlaceholder) {
            var BadgeListView = ListView.extend({
                tagName: 'div',

                template: HtmlUtils.template(badgePlaceholder),

                renderCollection: function() {
                    var self = this,
                        $row;

                    this.$el.empty();

                    // Split into two columns.
                    this.collection.each(function(badge, index) {
                        var $item;
                        if (index % 2 === 0) {
                            $row = $('<div class="row">');
                            this.$el.append($row);
                        }
                        $item = new BadgeView({
                            model: badge,
                            badgeMeta: this.badgeMeta,
                            ownProfile: this.ownProfile
                        }).render().el;

                        if ($row) {
                            $row.append($item);
                        }

                        this.itemViews.push($item);
                    }, this);
                    // Placeholder must always be at the end, and may need a new row.
                    if (!this.collection.hasNextPage()) {
                        // find_courses_url set by BadgeListContainer during initialization.
                        if (this.collection.length % 2 === 0) {
                            $row = $('<div class="row">');
                            this.$el.append($row);
                        }

                        if ($row) {
                            HtmlUtils.append(
                                $row,
                                this.template({find_courses_url: self.find_courses_url})
                            );
                        }
                    }
                    return this;
                }
            });

            return BadgeListView;
        });
}).call(this, define || RequireJS.define);
