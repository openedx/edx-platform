/**
 * This page is used to show the user an outline of the course.
 */
define([
    'jquery', 'underscore', 'gettext', 'js/views/pages/base_page', 'js/views/utils/xblock_utils',
    'js/views/course_outline', 'common/js/components/utils/view_utils', 'common/js/components/views/feedback_alert',
    'common/js/components/views/feedback_notification', 'js/views/course_highlights_enable'],
    function($, _, gettext, BasePage, XBlockViewUtils, CourseOutlineView, ViewUtils, AlertView, NoteView,
             CourseHighlightsEnableView
    ) {
        'use strict';
        var expandedLocators, CourseOutlinePage;

        CourseOutlinePage = BasePage.extend({
            // takes XBlockInfo as a model

            events: {
                'click .button-toggle-expand-collapse': 'toggleExpandCollapse'
            },

            /**
             * keep a running timeout counter of 5,000 milliseconds
             * for finding an element; see afterRender and scrollToElement function
             */
            findElementPollingTimeout: 5000,

            /**
             * used as the delay parameter to setTimeout in scrollToElement
             * function for polling for an element
             */
            pollingDelay: 100,

            options: {
                collapsedClass: 'is-collapsed'
            },

            // Extracting this to a variable allows comprehensive themes to replace or extend `CourseOutlineView`.
            outlineViewClass: CourseOutlineView,

            initialize: function() {
                var self = this;
                this.initialState = this.options.initialState;
                BasePage.prototype.initialize.call(this);
                this.$('.button-new').click(function(event) {
                    self.outlineView.handleAddEvent(event);
                });
                this.$('.button.button-reindex').click(function(event) {
                    self.handleReIndexEvent(event);
                });
                this.model.on('change', this.setCollapseExpandVisibility, this);
                $('.dismiss-button').bind('click', ViewUtils.deleteNotificationHandler(function() {
                    $('.wrapper-alert-announcement').removeClass('is-shown').addClass('is-hidden');
                }));
            },

            setCollapseExpandVisibility: function() {
                var has_content = this.hasContent(),
                    $collapseExpandButton = $('.button-toggle-expand-collapse');
                if (has_content) {
                    $collapseExpandButton.removeClass('is-hidden');
                } else {
                    $collapseExpandButton.addClass('is-hidden');
                }
            },

            renderPage: function() {
                var setInitialExpandState = function(xblockInfo, expandedLocators) {
                    if (xblockInfo.isCourse() || xblockInfo.isChapter()) {
                        expandedLocators.add(xblockInfo.get('id'));
                    }
                };

                this.setCollapseExpandVisibility();
                this.expandedLocators = expandedLocators;
                this.expandedLocators.clear();
                if (this.model.get('child_info')) {
                    _.each(this.model.get('child_info').children, function(childXBlockInfo) {
                        setInitialExpandState(childXBlockInfo, this.expandedLocators);
                    }, this);
                }
                setInitialExpandState(this.model, this.expandedLocators);

                if (this.initialState && this.initialState.expanded_locators) {
                    this.expandedLocators.addAll(this.initialState.expanded_locators);
                }

                /* globals course */
                if (this.model.get('highlights_enabled')) {
                    this.highlightsEnableView = new CourseHighlightsEnableView({
                        el: this.$('.status-highlights-enabled'),
                        model: this.model
                    });
                    this.highlightsEnableView.render();
                }

                this.outlineView = new this.outlineViewClass({
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

            afterRender: function() {
                this.scrollToElement();
            },

            /**
             * recursively poll for element specified by the URL fragment
             * at 100 millisecond intervals until element is found or
             * Polling is reached
             */
            scrollToElement: function () {
                this.findElementPollingTimeout -= this.pollingDelay;

                const elementID = window.location.hash.replace("#", "");

                if (this.findElementPollingTimeout > 0) {
                    if (elementID) {
                        const element = document.getElementById(elementID);
                        if (element) {
                            element.scrollIntoView();
                        } else {
                            setTimeout(this.scrollToElement, this.pollingDelay);
                        }
                    }
                }
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
                    var $element = $(domElement);
                    if (collapse) {
                        $element.addClass('is-collapsed');
                    } else {
                        $element.removeClass('is-collapsed');
                    }
                });
                if (this.model.get('child_info')) {
                    _.each(this.model.get('child_info').children, function(childXBlockInfo) {
                        if (collapse) {
                            this.expandedLocators.remove(childXBlockInfo.get('id'));
                        } else {
                            this.expandedLocators.add(childXBlockInfo.get('id'));
                        }
                    }, this);
                }
            },

            handleReIndexEvent: function(event) {
                var self = this;
                event.preventDefault();
                var $target = $(event.currentTarget);
                $target.css('cursor', 'wait');
                this.startReIndex($target.attr('href'))
                    .done(function(data) { self.onIndexSuccess(data); })
                    .fail(function(data) { self.onIndexError(data); })
                    .always(function() { $target.css('cursor', 'pointer'); });
            },

            startReIndex: function(reindex_url) {
                return $.ajax({
                    url: reindex_url,
                    method: 'GET',
                    global: false,
                    contentType: 'application/json; charset=utf-8',
                    dataType: 'json'
                });
            },

            onIndexSuccess: function(data) {
                var msg = new AlertView.Announcement({
                    title: gettext('Course Index'),
                    message: data.user_message
                });
                msg.show();
            },

            onIndexError: function(data) {
                var msg = new NoteView.Error({
                    title: gettext('There were errors reindexing course.'),
                    message: data.user_message
                });
                msg.show();
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
            add: function(locator) {
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
            remove: function(locator) {
                var index = this.locators.indexOf(locator);
                if (index >= 0) {
                    this.locators.splice(index, 1);
                }
            },

            /**
             * Returns true iff the locator is present in the set.
             */
            contains: function(locator) {
                return this.locators.indexOf(locator) >= 0;
            },

            /**
             * Clears all expanded locators from the set.
             */
            clear: function() {
                this.locators = [];
            }
        };

        return CourseOutlinePage;
    }); // end define();
