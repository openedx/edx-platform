/**
 * This page is used to show the user an outline of the course.
 */
define(["jquery", "underscore", "gettext", "js/views/pages/base_page", "js/views/utils/xblock_utils",
        "js/views/course_outline"],
    function ($, _, gettext, BasePage, XBlockViewUtils, CourseOutlineView) {
        var expandedLocators, CourseOutlinePage;

        CourseOutlinePage = BasePage.extend({
            // takes XBlockInfo as a model

            events: {
                "click .button-toggle-expand-collapse": "toggleExpandCollapse"
            },

            options: {
                collapsedClass: 'is-collapsed'
            },

            initialize: function() {
                var self = this;
                this.initialState = this.options.initialState;
                BasePage.prototype.initialize.call(this);
                this.$('.button-new').click(function(event) {
                    self.outlineView.handleAddEvent(event);
                });
                this.model.on('change', this.setCollapseExpandVisibility, this);
            },

            setCollapseExpandVisibility: function() {
                var has_content = this.hasContent(),
                    collapseExpandButton = $('.button-toggle-expand-collapse');
                if (has_content) {
                    collapseExpandButton.removeClass('is-hidden');
                } else {
                    collapseExpandButton.addClass('is-hidden');
                }
            },

            renderPage: function() {
                var setInitialExpandState = function (xblockInfo, expandedLocators) {
                    if (xblockInfo.isCourse() || xblockInfo.isChapter()) {
                        expandedLocators.add(xblockInfo.get('id'));
                    }
                };

                this.setCollapseExpandVisibility();
                this.expandedLocators = expandedLocators;
                this.expandedLocators.clear();
                if (this.model.get('child_info')) {
                    _.each(this.model.get('child_info').children, function (childXBlockInfo) {
                       setInitialExpandState(childXBlockInfo, this.expandedLocators);
                    }, this);
                }
                setInitialExpandState(this.model, this.expandedLocators);

                if (this.initialState && this.initialState.expanded_locators) {
                    this.expandedLocators.addAll(this.initialState.expanded_locators);
                }

                this.outlineView = new CourseOutlineView({
                    el: this.$('.outline'),
                    model: this.model,
                    isRoot: true,
                    initialState: this.initialState,
                    expandedLocators: this.expandedLocators
                });
                this.outlineView.render();
                this.outlineView.setViewState(this.initialState || {});
                return $.Deferred().resolve().promise();
            },

            hasContent: function() {
                return this.model.hasChildren();
            },

            toggleExpandCollapse: function(event) {
                var toggleButton = this.$('.button-toggle-expand-collapse'),
                    collapse = toggleButton.hasClass('collapse-all');
                event.preventDefault();
                toggleButton.toggleClass('collapse-all expand-all');
                this.$('.list-sections > li').each(function(index, domElement) {
                    var element = $(domElement);
                    if (collapse) {
                        element.addClass('is-collapsed');
                    } else {
                        element.removeClass('is-collapsed');
                    }
                });
                if (this.model.get('child_info')) {
                    _.each(this.model.get('child_info').children, function (childXBlockInfo) {
                        if (collapse) {
                            this.expandedLocators.remove(childXBlockInfo.get('id'));
                        }
                        else {
                            this.expandedLocators.add(childXBlockInfo.get('id'));
                        }
                    }, this);
                }
            }
        });

        /**
         * Represents the set of locators that should be expanded for the page.
         */
        expandedLocators = {
            locators: [],

            /**
             * Add the locator to the set if it is not already present.
             */
            add: function (locator) {
                if (!this.contains(locator)) {
                   this.locators.push(locator);
                }
            },

            /**
             * Accepts an array of locators and adds them all to the set if not already present.
             */
            addAll: function(locators) {
                _.each(locators, function(locator) {
                    this.add(locator);
                }, this);
            },

            /**
             * Remove the locator from the set if it is present.
             */
            remove: function (locator) {
                var index = this.locators.indexOf(locator);
                if (index >= 0) {
                    this.locators.splice(index, 1);
                }
            },

            /**
             * Returns true iff the locator is present in the set.
             */
            contains: function (locator) {
                return this.locators.indexOf(locator) >= 0;
            },

            /**
             * Clears all expanded locators from the set.
             */
            clear: function () {
                this.locators = [];
            }
        };

        return CourseOutlinePage;
    }); // end define();
