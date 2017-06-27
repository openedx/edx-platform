(function(define) {
    'use strict';
    define(['jquery', 'underscore', 'backbone', 'gettext', 'js/discussions_management/views/divided_discussions',
        'edx-ui-toolkit/js/utils/html-utils', 'js/vendor/jquery.qubit'],
            function($, _, Backbone, gettext, DividedDiscussionConfigurationView, HtmlUtils) {
                var InlineDiscussionsView = DividedDiscussionConfigurationView.extend({
                    events: {
                        'change .check-discussion-category': 'setSaveButton',
                        'change .check-discussion-subcategory-inline': 'setSaveButton',
                        'click .cohort-inline-discussions-form .action-save': 'saveInlineDiscussionsForm',
                        'change .check-all-inline-discussions': 'setAllInlineDiscussions',
                        'change .check-cohort-inline-discussions': 'setSomeInlineDiscussions'
                    },

                    initialize: function(options) {
                        this.template = HtmlUtils.template($('#divided-discussions-inline-tpl').text());
                        this.discussionSettings = options.discussionSettings;
                    },

                    render: function() {
                        var inlineDiscussions = this.model.get('inline_discussions'),
                            alwaysDivideInlineDiscussions = this.discussionSettings.get(
                                'always_divide_inline_discussions'
                            );

                        HtmlUtils.setHtml(this.$('.inline-discussions-nav'), this.template({
                            inlineDiscussionTopicsHtml: this.getInlineDiscussionsHtml(inlineDiscussions),
                            alwaysDivideInlineDiscussions: alwaysDivideInlineDiscussions
                        }));

                        // Provides the semantics for a nested list of tri-state checkboxes.
                        // When attached to a jQuery element it listens for change events to
                        // input[type=checkbox] elements, and updates the checked and indeterminate
                        // based on the checked values of any checkboxes in child elements of the DOM.
                        this.$('ul.inline-topics').qubit();

                        this.setElementsEnabled(alwaysDivideInlineDiscussions, true);
                    },

                    /**
                    * Generate html list for inline discussion topics.
                    * @params {object} inlineDiscussions - inline discussions object from server.
                    * @returns {HtmlSnippet} - HTML for inline discussion topics.
                    */
                    getInlineDiscussionsHtml: function(inlineDiscussions) {
                        var categoryTemplate = HtmlUtils.template($('#cohort-discussions-category-tpl').html()),
                            entryTemplate = HtmlUtils.template($('#cohort-discussions-subcategory-tpl').html()),
                            isCategoryCohorted = false,
                            children = inlineDiscussions.children,
                            entries = inlineDiscussions.entries,
                            subcategories = inlineDiscussions.subcategories;

                        return HtmlUtils.joinHtml.apply(this, _.map(children, function(child) {
                            var htmlSnippet = '',
                                name = child[0], // child[0] is the category name
                                type = child[1], // child[1] is the type (i.e. 'entry' or 'subcategory')
                                entry;
                            if (entries && _.has(entries, name) && type === 'entry') {
                                entry = entries[name];
                                htmlSnippet = entryTemplate({
                                    name: name,
                                    id: entry.id,
                                    is_divided: entry.is_divided,
                                    type: 'inline'
                                });
                            } else { // subcategory
                                htmlSnippet = categoryTemplate({
                                    name: name,
                                    entriesHtml: this.getInlineDiscussionsHtml(subcategories[name]),
                                    isCategoryCohorted: isCategoryCohorted
                                });
                            }
                            return htmlSnippet;
                        }, this));
                    },

                    /**
                    * Enable/Disable the inline discussion elements.
                    *
                    * Disables the category and sub-category checkboxes.
                    * Enables the save button.
                    */
                    setAllInlineDiscussions: function(event) {
                        event.preventDefault();
                        this.setElementsEnabled(($(event.currentTarget).prop('checked')), false);
                    },

                    /**
                    * Enables the inline discussion elements.
                    *
                    * Enables the category and sub-category checkboxes.
                    * Enables the save button.
                    */
                    setSomeInlineDiscussions: function(event) {
                        event.preventDefault();
                        this.setElementsEnabled(!($(event.currentTarget).prop('checked')), false);
                    },

                    /**
                    * Enable/Disable the inline discussion elements.
                    *
                    * Enable/Disable the category and sub-category checkboxes.
                    * Enable/Disable the save button.
                    * @param {bool} enableCheckboxes - The flag to enable/disable the checkboxes.
                    * @param {bool} enableSaveButton - The flag to enable/disable the save button.
                    */
                    setElementsEnabled: function(enableCheckboxes, enableSaveButton) {
                        this.setDisabled(this.$('.check-discussion-category'), enableCheckboxes);
                        this.setDisabled(this.$('.check-discussion-subcategory-inline'), enableCheckboxes);
                        this.setDisabled(this.$('.cohort-inline-discussions-form .action-save'), enableSaveButton);
                    },

                    /**
                    * Enables the save button for inline discussions.
                    */
                    setSaveButton: function() {
                        this.setDisabled(this.$('.cohort-inline-discussions-form .action-save'), false);
                    },

                    /**
                    * Sends the dividedInlineDiscussions to the server and renders the view.
                    */
                    saveInlineDiscussionsForm: function(event) {
                        var self = this,
                            dividedInlineDiscussions = self.getDividedDiscussions(
                                '.check-discussion-subcategory-inline:checked'
                            ),
                            fieldData = {
                                divided_inline_discussions: dividedInlineDiscussions,
                                always_divide_inline_discussions: self.$(
                                    '.check-all-inline-discussions'
                                ).prop('checked')
                            };

                        event.preventDefault();

                        self.saveForm(self.$('.inline-discussion-topics'), fieldData)
                            .done(function() {
                                self.model.fetch()
                                    .done(function() {
                                        self.render();
                                        self.showMessage(gettext('Your changes have been saved.'),
                                            self.$('.inline-discussion-topics'));
                                    }).fail(function() {
                                        var errorMessage = gettext("We've encountered an error. Refresh your browser and then try again."); // eslint-disable-line max-len
                                        self.showMessage(errorMessage, self.$('.inline-discussion-topics'), 'error');
                                    });
                            });
                    }

                });
                return InlineDiscussionsView;
            });
}).call(this, define || RequireJS.define);
