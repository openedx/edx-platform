var edx = edx || {};

(function ($, _, Backbone, gettext, interpolate_text, CohortDiscussionsView) {
    'use strict';

    edx.groups = edx.groups || {};

    edx.groups.InlineDiscussionsView = CohortDiscussionsView.extend({
        events: {
            'change .check-discussion-category': 'changeInlineDiscussionsCategory',
            'change .check-discussion-subcategory-inline': 'changeInlineDiscussionsSubCategory',
            'click .cohort-inline-discussions-form .action-save': 'saveInlineDiscussionsForm',
            'change .check-all-inline-discussions': 'changeAllInlineDiscussions',
            'change .check-cohort-inline-discussions': 'changeCohortInlineDiscussions'
        },

        initialize: function (options) {
            this.template = _.template($('#cohort-discussions-inline-tpl').text());
            this.cohortSettings = options.cohortSettings;
        },

        render: function () {
            var alwaysCohortInlineDiscussions = this.cohortSettings.get('always_cohort_inline_discussions');

            this.$('.cohort-inline-discussions-nav').html(this.template({
                inlineDiscussionTopics: this.getInlineDiscussions(this.model.get('inline_discussions')),
                alwaysCohortInlineDiscussions:alwaysCohortInlineDiscussions
            }));

            $('ul.inline-topics').qubit();

            this.setDisabled(this.$('.cohort-inline-discussions-form .action-save'), false);
            if (alwaysCohortInlineDiscussions) {
                this.setDisabled(this.$('.check-discussion-category'), false);
                this.setDisabled(this.$('.check-discussion-subcategory-inline'), false);
            }
        },

        getInlineDiscussions: function (categoryMap) {
            var categoryTemplate = _.template($('#cohort-discussions-category-tpl').html()),
                entryTemplate = _.template($('#cohort-discussions-subcategory-tpl').html()),
                isCategoryCohorted = false,
                children = categoryMap.children,
                entries = categoryMap.entries,
                subcategories = categoryMap.subcategories;

            return _.map(children, function (name) {
                var html = '', entry;
                if (entries && _.has(entries, name)) {
                    entry = entries[name];
                    html = entryTemplate({
                        name: name,
                        id: entry.id,
                        is_cohorted: entry.is_cohorted,
                        type: 'inline'
                    });
                } else { // subcategory
                    html = categoryTemplate({
                        name: name,
                        entries: this.getInlineDiscussions(subcategories[name]),
                        isCategoryCohorted: isCategoryCohorted
                    });
                }
                return html;
            }, this).join('');
        },

        changeAllInlineDiscussions: function(event) {
            event.preventDefault();
            this.toggleInlineDiscussions(!($(event.currentTarget).prop('checked')));
        },

        changeCohortInlineDiscussions: function(event) {
            event.preventDefault();
            this.toggleInlineDiscussions(($(event.currentTarget).prop('checked')));
        },

        toggleInlineDiscussions: function(enable) {
            this.setDisabled(this.$('.check-discussion-category'), enable);
            this.setDisabled(this.$('.check-discussion-subcategory-inline'), enable);
            this.setDisabled(this.$('.cohort-inline-discussions-form .action-save'), true);
        },

        changeInlineDiscussionsCategory: function(event) {
            var $selectedCategory = $(event.currentTarget);

            if (!$selectedCategory.prop('checked')) {
                $('.check-all-inline-discussions').prop('checked', false);
            }
        },

        changeInlineDiscussionsSubCategory: function (event) {
            var $selectedTopic = $(event.currentTarget);
            if (!$selectedTopic.prop('checked')) {
                $('.check-all-inline-discussions').prop('checked', false);
            }
            this.setDisabled(this.$('.cohort-inline-discussions-form .action-save'), true);
        },

        saveInlineDiscussionsForm: function (event) {
            event.preventDefault();

            var self = this;
            self.setCohortedDiscussions('.check-discussion-subcategory-inline:checked');

            this.cohortSettings.set({
                cohorted_inline_discussions: self.cohortedDiscussions,
                always_cohort_inline_discussions: self.$('.check-all-inline-discussions').prop('checked')
            });

            self.saveForm(self.$('.inline-discussion-topics'))
                .done(function () {
                    self.model.fetch().done(function () {
                        self.render();
                        self.showMessage(gettext('Changes Saved.'), self.$('.inline-discussion-topics'));
                    });
                });
        }

    });
}).call(this, $, _, Backbone, gettext, interpolate_text, edx.groups.CohortDiscussionsView);
