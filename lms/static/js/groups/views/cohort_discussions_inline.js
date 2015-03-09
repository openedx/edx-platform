var edx = edx || {};

(function ($, _, Backbone, gettext, interpolate_text, CohortDiscussionsView) {
    'use strict';

    edx.groups = edx.groups || {};

    edx.groups.InlineDiscussionsView = CohortDiscussionsView.extend({
        events: {
            'click .cohort-inline-discussions-form .action-save': 'saveInlineDiscussionsForm',
            'change .check-all-inline-discussions': 'setAllInlineDiscussions',
            'change .check-cohort-inline-discussions': 'setSomeInlineDiscussions'
        },

        initialize: function (options) {
            this.template = _.template($('#cohort-discussions-inline-tpl').text());
            this.cohortSettings = options.cohortSettings;
        },

        render: function () {
            var alwaysCohortInlineDiscussions = this.cohortSettings.get('always_cohort_inline_discussions');

            this.$('.cohort-inline-discussions-nav').html(this.template({
                inlineDiscussionTopics: this.getInlineDiscussionsHtml(this.model.get('inline_discussions')),
                alwaysCohortInlineDiscussions:alwaysCohortInlineDiscussions
            }));

            // Provides the semantics for a nested list of tri-state checkboxes.
            // When attached to a jQuery element it listens for change events to
            // input[type=checkbox] elements, and updates the checked and indeterminate
            // based on the checked values of any checkboxes in child elements of the DOM.
            $('ul.inline-topics').qubit();

            this.setElementsEnabled(alwaysCohortInlineDiscussions, true);
        },

        /**
         Returns the html list for inline discussion topics.

         Args:
            inlineDiscussions (object): inline discussions object from server
                with attributes 'entries', 'children' & 'subcategories'.

         Returns:
            HTML list for inline discussion topics.
        **/
        getInlineDiscussionsHtml: function (inlineDiscussions) {
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
                        entries: this.getInlineDiscussionsHtml(subcategories[name]),
                        isCategoryCohorted: isCategoryCohorted
                    });
                }
                return html;
            }, this).join('');
        },

        /**
         Disables the discussion category checkboxes.
         Disables the discussion sub-category checkboxes.
         Enables the save button for inline discussion topics.
        **/
        setAllInlineDiscussions: function(event) {
            event.preventDefault();
            this.setElementsEnabled(($(event.currentTarget).prop('checked')), false);
        },

        /**
         Enables the discussion category checkboxes.
         Enables the discussion sub-category checkboxes.
         Enables the save button for inline discussion topics.

         Args:
            disable (Bool): The flag to enable/disable the elements.
        **/
        setSomeInlineDiscussions: function(event) {
            event.preventDefault();
            this.setElementsEnabled(!($(event.currentTarget).prop('checked')), false);
        },

        /**
         Enable/Disable the discussion category checkboxes.
         Enable/Disable the discussion sub-category checkboxes.
         Enable/Disable the save button for inline discussion topics.

         Args:
            enable_checkboxes (Bool): The flag to enable/disable the checkboxes.
            enable_save_button (Bool): The flag to enable/disable the save button.
        **/
        setElementsEnabled: function(enable_checkboxes, enable_save_button) {
            this.setDisabled(this.$('.check-discussion-category'), enable_checkboxes);
            this.setDisabled(this.$('.check-discussion-subcategory-inline'), enable_checkboxes);
            this.setDisabled(this.$('.cohort-inline-discussions-form .action-save'), enable_save_button);
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
