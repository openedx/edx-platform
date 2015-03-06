var edx = edx || {};

(function ($, _, Backbone, gettext, interpolate_text, CohortDiscussionsView) {
    'use strict';

    edx.groups = edx.groups || {};

    edx.groups.InlineDiscussionsView = CohortDiscussionsView.extend({
        events: {
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

            this.setDisabled(this.$('.cohort-inline-discussions-form .action-save'), true);
            if (alwaysCohortInlineDiscussions) {
                this.setDisabled(this.$('.check-discussion-category'), true);
                this.setDisabled(this.$('.check-discussion-subcategory-inline'), true);
            }
        },

        /**
         Returns the html list for inline discussion topics.

         Args:
            inlineDiscussions (object): inline discussions object from server
                with attributes 'entries', 'children' & 'subcategories'.

         Returns:
            HTML list for inline discussion topics.
        **/
        getInlineDiscussions: function (inlineDiscussions) {
            var categoryTemplate = _.template($('#cohort-discussions-category-tpl').html()),
                entryTemplate = _.template($('#cohort-discussions-subcategory-tpl').html()),
                isCategoryCohorted = false,
                children = inlineDiscussions.children,
                entries = inlineDiscussions.entries,
                subcategories = inlineDiscussions.subcategories;

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

        /**
         Enable/Disable the discussion category checkboxes.
         Enable/Disable the discussion sub-category checkboxes.
         Enable/Disable the save button for inline discussion topics.

         Args:
            disable (Bool): The flag to enable/disable the elements.
        **/
        changeAllInlineDiscussions: function(event) {
            event.preventDefault();
            this.toggleInlineDiscussions(($(event.currentTarget).prop('checked')));
        },

        /**
         Enable/Disable the discussion category checkboxes.
         Enable/Disable the discussion sub-category checkboxes.
         Enable/Disable the save button for inline discussion topics.

         Args:
            disable (Bool): The flag to enable/disable the elements.
        **/
        changeCohortInlineDiscussions: function(event) {
            event.preventDefault();
            this.toggleInlineDiscussions(!($(event.currentTarget).prop('checked')));
        },

        /**
         Enable/Disable the discussion category checkboxes.
         Enable/Disable the discussion sub-category checkboxes.
         Enable/Disable the save button for inline discussion topics.

         Args:
            disable (Bool): The flag to enable/disable the elements.
        **/
        toggleInlineDiscussions: function(disable) {
            this.setDisabled(this.$('.check-discussion-category'), disable);
            this.setDisabled(this.$('.check-discussion-subcategory-inline'), disable);
            this.setDisabled(this.$('.cohort-inline-discussions-form .action-save'), false);
        },

        /**
         Sends the cohorted_inline_discussions to the server and renders the view.
        **/
        saveInlineDiscussionsForm: function (event) {
            event.preventDefault();

            var self = this;
            var cohortedInlineDiscussions = self.getCohortedDiscussions(
                '.check-discussion-subcategory-inline:checked'
            );

            this.cohortSettings.set({
                cohorted_inline_discussions: cohortedInlineDiscussions,
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
