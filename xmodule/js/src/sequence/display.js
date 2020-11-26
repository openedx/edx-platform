/* eslint-disable no-underscore-dangle */
/* globals Logger, interpolate */

(function() {
    'use strict';

    this.Sequence = (function() {
        function Sequence(element) {
            var self = this;

            this.removeBookmarkIconFromActiveNavItem = function(event) {
                return Sequence.prototype.removeBookmarkIconFromActiveNavItem.apply(self, [event]);
            };
            this.addBookmarkIconToActiveNavItem = function(event) {
                return Sequence.prototype.addBookmarkIconToActiveNavItem.apply(self, [event]);
            };
            this._change_sequential = function(direction, event) {
                return Sequence.prototype._change_sequential.apply(self, [direction, event]);
            };
            this.selectPrevious = function(event) {
                return Sequence.prototype.selectPrevious.apply(self, [event]);
            };
            this.selectNext = function(event) {
                return Sequence.prototype.selectNext.apply(self, [event]);
            };
            this.goto = function(event) {
                return Sequence.prototype.goto.apply(self, [event]);
            };
            this.toggleArrows = function() {
                return Sequence.prototype.toggleArrows.apply(self);
            };
            this.addToUpdatedProblems = function(problemId, newContentState, newState) {
                return Sequence.prototype.addToUpdatedProblems.apply(self, [problemId, newContentState, newState]);
            };
            this.hideTabTooltip = function(event) {
                return Sequence.prototype.hideTabTooltip.apply(self, [event]);
            };
            this.displayTabTooltip = function(event) {
                return Sequence.prototype.displayTabTooltip.apply(self, [event]);
            };
            this.arrowKeys = {
                LEFT: 37,
                UP: 38,
                RIGHT: 39,
                DOWN: 40
            };

            this.updatedProblems = {};
            this.requestToken = $(element).data('request-token');
            this.el = $(element).find('.sequence');
            this.path = $('.path');
            this.contents = this.$('.seq_contents');
            this.content_container = this.$('#seq_content');
            this.sr_container = this.$('.sr-is-focusable');
            this.num_contents = this.contents.length;
            this.id = this.el.data('id');
            this.ajaxUrl = this.el.data('ajax-url');
            this.nextUrl = this.el.data('next-url');
            this.prevUrl = this.el.data('prev-url');
            this.savePosition = this.el.data('save-position');
            this.showCompletion = this.el.data('show-completion');
            this.keydownHandler($(element).find('#sequence-list .tab'));
            this.base_page_title = ($('title').data('base-title') || '').trim();
            this.bind();
            this.render(parseInt(this.el.data('position'), 10));
        }

        Sequence.prototype.$ = function(selector) {
            return $(selector, this.el);
        };

        Sequence.prototype.bind = function() {
            this.$('#sequence-list .nav-item').click(this.goto);
            this.$('#sequence-list .nav-item').keypress(this.keyDownHandler);
            this.el.on('bookmark:add', this.addBookmarkIconToActiveNavItem);
            this.el.on('bookmark:remove', this.removeBookmarkIconFromActiveNavItem);
            this.$('#sequence-list .nav-item').on('focus mouseenter', this.displayTabTooltip);
            this.$('#sequence-list .nav-item').on('blur mouseleave', this.hideTabTooltip);
        };

        Sequence.prototype.previousNav = function(focused, index) {
            var $navItemList,
                $sequenceList = $(focused).parent().parent();
            if (index === 0) {
                $navItemList = $sequenceList.find('li').last();
            } else {
                $navItemList = $sequenceList.find('li:eq(' + index + ')').prev();
            }
            $sequenceList.find('.tab').removeClass('visited').removeClass('focused');
            $navItemList.find('.tab').addClass('focused').focus();
        };

        Sequence.prototype.nextNav = function(focused, index, total) {
            var $navItemList,
                $sequenceList = $(focused).parent().parent();
            if (index === total) {
                $navItemList = $sequenceList.find('li').first();
            } else {
                $navItemList = $sequenceList.find('li:eq(' + index + ')').next();
            }
            $sequenceList.find('.tab').removeClass('visited').removeClass('focused');
            $navItemList.find('.tab').addClass('focused').focus();
        };

        Sequence.prototype.keydownHandler = function(element) {
            var self = this;
            element.keydown(function(event) {
                var key = event.keyCode,
                    $focused = $(event.currentTarget),
                    $sequenceList = $focused.parent().parent(),
                    index = $sequenceList.find('li')
                        .index($focused.parent()),
                    total = $sequenceList.find('li')
                        .size() - 1;
                switch (key) {
                case self.arrowKeys.LEFT:
                    event.preventDefault();
                    self.previousNav($focused, index);
                    break;

                case self.arrowKeys.RIGHT:
                    event.preventDefault();
                    self.nextNav($focused, index, total);
                    break;

                // no default
                }
            });
        };

        Sequence.prototype.displayTabTooltip = function(event) {
            $(event.currentTarget).find('.sequence-tooltip').removeClass('sr');
        };

        Sequence.prototype.hideTabTooltip = function(event) {
            $(event.currentTarget).find('.sequence-tooltip').addClass('sr');
        };

        Sequence.prototype.updatePageTitle = function() {
            // update the page title to include the current section
            var currentUnitTitle,
                newPageTitle,
                positionLink = this.link_for(this.position);

            if (positionLink && positionLink.data('page-title')) {
                currentUnitTitle = positionLink.data('page-title');
                newPageTitle = currentUnitTitle + ' | ' + this.base_page_title;

                if (newPageTitle !== document.title) {
                    document.title = newPageTitle;
                }

                // Update the title section of the breadcrumb
                $('.nav-item-sequence').text(currentUnitTitle);
            }
        };

        Sequence.prototype.hookUpContentStateChangeEvent = function() {
            var self = this;

            return $('.problems-wrapper').bind('contentChanged', function(event, problemId, newContentState, newState) {
                return self.addToUpdatedProblems(problemId, newContentState, newState);
            });
        };

        Sequence.prototype.addToUpdatedProblems = function(problemId, newContentState, newState) {
            /**
            * Used to keep updated problem's state temporarily.
            * params:
            *   'problem_id' is problem id.
            *   'new_content_state' is the updated content of the problem.
            *   'new_state' is the updated state of the problem.
            */

            // initialize for the current sequence if there isn't any updated problem for this position.
            if (!this.anyUpdatedProblems(this.position)) {
                this.updatedProblems[this.position] = {};
            }

            // Now, put problem content and score against problem id for current active sequence.
            this.updatedProblems[this.position][problemId] = [newContentState, newState];
        };

        Sequence.prototype.anyUpdatedProblems = function(position) {
            /**
            * check for the updated problems for given sequence position.
            * params:
            *   'position' can be any sequence position.
            */
            return typeof(this.updatedProblems[position]) !== 'undefined';
        };

        Sequence.prototype.enableButton = function(buttonClass, buttonAction) {
            this.$(buttonClass)
                .removeClass('disabled')
                .removeAttr('disabled')
                .click(buttonAction);
        };

        Sequence.prototype.disableButton = function(buttonClass) {
            this.$(buttonClass).addClass('disabled').attr('disabled', true);
        };

        Sequence.prototype.updateButtonState = function(buttonClass, buttonAction, isAtBoundary, boundaryUrl) {
            if (isAtBoundary && boundaryUrl === 'None') {
                this.disableButton(buttonClass);
            } else {
                this.enableButton(buttonClass, buttonAction);
            }
        };

        Sequence.prototype.toggleArrows = function() {
            var isFirstTab, isLastTab, nextButtonClass, previousButtonClass;

            this.$('.sequence-nav-button').unbind('click');

            // previous button
            isFirstTab = this.position === 1;
            previousButtonClass = '.sequence-nav-button.button-previous';
            this.updateButtonState(previousButtonClass, this.selectPrevious, isFirstTab, this.prevUrl);

            // next button
            // use inequality in case contents.length is 0 and position is 1.
            isLastTab = this.position >= this.contents.length;
            nextButtonClass = '.sequence-nav-button.button-next';
            this.updateButtonState(nextButtonClass, this.selectNext, isLastTab, this.nextUrl);
        };

        Sequence.prototype.render = function(newPosition) {
            var bookmarked, currentTab, modxFullUrl, sequenceLinks,
                self = this;
            if (this.position !== newPosition) {
                if (this.position) {
                    this.mark_visited(this.position);
                    if (this.showCompletion) {
                        this.update_completion(this.position);
                    }
                    if (this.savePosition) {
                        modxFullUrl = '' + this.ajaxUrl + '/goto_position';
                        $.postWithPrefix(modxFullUrl, {
                            position: newPosition
                        });
                    }
                }

                // On Sequence change, fire custom event 'sequence:change' on element.
                // Added for aborting video bufferization, see ../video/10_main.js
                this.el.trigger('sequence:change');
                this.mark_active(newPosition);
                currentTab = this.contents.eq(newPosition - 1);
                bookmarked = this.el.find('.active .bookmark-icon').hasClass('bookmarked');

                // update the data-attributes with latest contents only for updated problems.
                this.content_container
                    .html(currentTab.text())  // xss-lint: disable=javascript-jquery-html
                    .attr('aria-labelledby', currentTab.attr('aria-labelledby'))
                    .data('bookmarked', bookmarked);


                if (this.anyUpdatedProblems(newPosition)) {
                    $.each(this.updatedProblems[newPosition], function(problemId, latestData) {
                        var latestContent, latestResponse;
                        latestContent = latestData[0];
                        latestResponse = latestData[1];
                        self.content_container
                            .find("[data-problem-id='" + problemId + "']")
                            .data('content', latestContent)
                            .data('problem-score', latestResponse.current_score)
                            .data('problem-total-possible', latestResponse.total_possible)
                            .data('attempts-used', latestResponse.attempts_used);
                    });
                }
                XBlock.initializeBlocks(this.content_container, this.requestToken);

                // For embedded circuit simulator exercises in 6.002x
                if (window.hasOwnProperty('update_schematics')) {
                    window.update_schematics();
                }
                this.position = newPosition;
                this.toggleArrows();
                this.hookUpContentStateChangeEvent();
                this.updatePageTitle();
                sequenceLinks = this.content_container.find('a.seqnav');
                sequenceLinks.click(this.goto);

                this.sr_container.focus();
            }
        };

        Sequence.prototype.goto = function(event) {
            var alertTemplate, alertText, isBottomNav, newPosition, widgetPlacement;
            event.preventDefault();

            // Links from courseware <a class='seqnav' href='n'>...</a>, was .target_tab
            if ($(event.currentTarget).hasClass('seqnav')) {
                newPosition = $(event.currentTarget).attr('href');
            } else if ($(event.currentTarget).data('href') !== undefined) {
                location.href = $(event.currentTarget).data('href');
                return true;
            // Tab links generated by backend template
            } else {
                newPosition = $(event.currentTarget).data('element');
            }

            if ((newPosition >= 1) && (newPosition <= this.num_contents)) {
                isBottomNav = $(event.target).closest('nav[class="sequence-bottom"]').length > 0;

                if (isBottomNav) {
                    widgetPlacement = 'bottom';
                } else {
                    widgetPlacement = 'top';
                }

                // Formerly known as seq_goto
                Logger.log('edx.ui.lms.sequence.tab_selected', {
                    current_tab: this.position,
                    target_tab: newPosition,
                    tab_count: this.num_contents,
                    id: this.id,
                    widget_placement: widgetPlacement
                });

                // On Sequence change, destroy any existing polling thread
                // for queued submissions, see ../capa/display.js
                if (window.queuePollerID) {
                    window.clearTimeout(window.queuePollerID);
                    delete window.queuePollerID;
                }
                this.render(newPosition);
            } else {
                alertTemplate = gettext('Sequence error! Cannot navigate to %(tab_name)s in the current SequenceModule. Please contact the course staff.');  // eslint-disable-line max-len
                alertText = interpolate(alertTemplate, {
                    tab_name: newPosition
                }, true);
                alert(alertText);  // eslint-disable-line no-alert
            }
        };

        Sequence.prototype.selectNext = function(event) {
            this._change_sequential('next', event);
        };

        Sequence.prototype.selectPrevious = function(event) {
            this._change_sequential('previous', event);
        };

        // `direction` can be 'previous' or 'next'
        Sequence.prototype._change_sequential = function(direction, event) {
            var analyticsEventName, isBottomNav, newPosition, offset, targetUrl, widgetPlacement;

            // silently abort if direction is invalid.
            if (direction !== 'previous' && direction !== 'next') {
                return;
            }
            event.preventDefault();
            analyticsEventName = 'edx.ui.lms.sequence.' + direction + '_selected';
            isBottomNav = $(event.target).closest('nav[class="sequence-bottom"]').length > 0;

            if (isBottomNav) {
                widgetPlacement = 'bottom';
            } else {
                widgetPlacement = 'top';
            }

            if ((direction === 'next') && (this.position >= this.contents.length)) {
                targetUrl = this.nextUrl;
            } else if ((direction === 'previous') && (this.position === 1)) {
                targetUrl = this.prevUrl;
            }

            // Formerly known as seq_next and seq_prev
            Logger.log(analyticsEventName, {
                id: this.id,
                current_tab: this.position,
                tab_count: this.num_contents,
                widget_placement: widgetPlacement
            }).always(function() {
                if (targetUrl) {
                    // Wait to load the new page until we've attempted to log the event
                    window.location.href = targetUrl;
                }
            });

            // If we're staying on the page, no need to wait for the event logging to finish
            if (!targetUrl) {
                // If the bottom nav is used, scroll to the top of the page on change.
                if (isBottomNav) {
                    $.scrollTo(0, 150);
                }

                offset = {
                    next: 1,
                    previous: -1
                };

                newPosition = this.position + offset[direction];
                this.render(newPosition);
            }
        };

        Sequence.prototype.link_for = function(position) {
            return this.$('#sequence-list .nav-item[data-element=' + position + ']');
        };

        Sequence.prototype.mark_visited = function(position) {
            // Don't overwrite class attribute to avoid changing Progress class
            var element = this.link_for(position);
            element.attr({tabindex: '-1', 'aria-selected': 'false', 'aria-expanded': 'false'})
                .removeClass('inactive')
                .removeClass('active')
                .removeClass('focused')
                .addClass('visited');
        };

        Sequence.prototype.update_completion = function(position) {
            var element = this.link_for(position);
            var completionUrl = this.ajaxUrl + '/get_completion';
            var usageKey = element[0].attributes['data-id'].value;
            var completionIndicators = element.find('.check-circle');
            if (completionIndicators.length) {
                $.postWithPrefix(completionUrl, {
                    usage_key: usageKey
                }, function(data) {
                    if (data.complete === true) {
                        completionIndicators.removeClass('is-hidden');
                    }
                });
            }
        };

        Sequence.prototype.mark_active = function(position) {
            // Don't overwrite class attribute to avoid changing Progress class
            var element = this.link_for(position);
            element.attr({tabindex: '0', 'aria-selected': 'true', 'aria-expanded': 'true'})
                .removeClass('inactive')
                .removeClass('visited')
                .removeClass('focused')
                .addClass('active');
            this.$('.sequence-list-wrapper').focus();
        };

        Sequence.prototype.addBookmarkIconToActiveNavItem = function(event) {
            event.preventDefault();
            this.el.find('.nav-item.active .bookmark-icon').removeClass('is-hidden').addClass('bookmarked');
            this.el.find('.nav-item.active .bookmark-icon-sr').text(gettext('Bookmarked'));
        };

        Sequence.prototype.removeBookmarkIconFromActiveNavItem = function(event) {
            event.preventDefault();
            this.el.find('.nav-item.active .bookmark-icon').removeClass('bookmarked').addClass('is-hidden');
            this.el.find('.nav-item.active .bookmark-icon-sr').text('');
        };

        return Sequence;
    }());
}).call(this);
