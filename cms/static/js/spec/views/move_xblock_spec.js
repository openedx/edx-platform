define(['jquery', 'underscore', 'edx-ui-toolkit/js/utils/spec-helpers/ajax-helpers',
        'common/js/spec_helpers/template_helpers', 'common/js/spec_helpers/view_helpers',
        'js/views/modals/move_xblock_modal', 'edx-ui-toolkit/js/utils/html-utils',
        'edx-ui-toolkit/js/utils/string-utils', 'js/models/xblock_info'],
    function($, _, AjaxHelpers, TemplateHelpers, ViewHelpers, MoveXBlockModal, HtmlUtils, StringUtils, XBlockInfo) {
        'use strict';
        describe('MoveXBlock', function() {
            var modal, showModal, renderViews, createXBlockInfo, createCourseOutline, courseOutlineOptions,
                parentChildMap, categoryMap, createChildXBlockInfo, xblockAncestorInfo, courseOutline,
                verifyBreadcrumbViewInfo, verifyListViewInfo, getDisplayedInfo, clickForwardButton,
                clickBreadcrumbButton, verifyXBlockInfo, nextCategory, verifyMoveEnabled, getSentRequests,
                verifyNotificationStatus, sendMoveXBlockRequest, moveXBlockWithSuccess,
                verifyConfirmationFeedbackTitleHtml, verifyConfirmationFeedbackRedirectLinkHtml,
                verifyUndoConfirmationFeedbackTitleHtml, verifyConfirmationFeedbackUndoMoveActionHtml,
                sourceDisplayName = 'component_display_name_0',
                sourceLocator = 'component_ID_0',
                sourceParentLocator = 'unit_ID_0';

            parentChildMap = {
                course: 'section',
                section: 'subsection',
                subsection: 'unit',
                unit: 'component'
            };

            categoryMap = {
                section: 'chapter',
                subsection: 'sequential',
                unit: 'vertical',
                component: 'component'
            };

            courseOutlineOptions = {
                section: 2,
                subsection: 2,
                unit: 2,
                component: 2
            };

            xblockAncestorInfo = {
                ancestors: [
                    {
                        category: 'vertical',
                        display_name: 'unit_display_name_0',
                        id: 'unit_ID_0'
                    },
                    {
                        category: 'sequential',
                        display_name: 'subsection_display_name_0',
                        id: 'subsection_ID_0'
                    },
                    {
                        category: 'chapter',
                        display_name: 'section_display_name_0',
                        id: 'section_ID_0'
                    },
                    {
                        category: 'course',
                        display_name: 'Demo Course',
                        id: 'COURSE_ID_101'
                    }
                ]
            };

            beforeEach(function() {
                setFixtures("<div id='page-alert'></div>");
                TemplateHelpers.installTemplates([
                    'basic-modal',
                    'modal-button',
                    'move-xblock-modal'
                ]);
                courseOutline = createCourseOutline(courseOutlineOptions);
                showModal();
            });

            afterEach(function() {
                modal.hide();
                courseOutline = null;
            });

            showModal = function() {
                modal = new MoveXBlockModal({
                    sourceXBlockInfo: new XBlockInfo({
                        id: sourceLocator,
                        display_name: sourceDisplayName,
                        category: 'component'
                    }),
                    sourceParentXBlockInfo: new XBlockInfo({
                        id: sourceParentLocator,
                        display_name: 'unit_display_name_0',
                        category: 'vertical'
                    }),
                    XBlockUrlRoot: '/xblock'
                });
                modal.show();
            };

            /**
             * Create child XBlock info.
             *
             * @param {String} category         XBlock category
             * @param {Object} outlineOptions   options according to which outline was created
             * @param {Object} xblockIndex      XBlock Index
             * @returns
             */
            createChildXBlockInfo = function(category, outlineOptions, xblockIndex) {
                var childInfo = {
                    category: categoryMap[category],
                    display_name: category + '_display_name_' + xblockIndex,
                    id: category + '_ID_' + xblockIndex
                };
                return createXBlockInfo(parentChildMap[category], outlineOptions, childInfo);
            };

            /**
             * Create parent XBlock info.
             *
             * @param {String} category         XBlock category
             * @param {Object} outlineOptions   options according to which outline was created
             * @param {Object} outline          ouline info being constructed
             * @returns {Object}
             */
            createXBlockInfo = function(category, outlineOptions, outline) {
                var childInfo = {
                        category: categoryMap[category],
                        display_name: category,
                        children: []
                    },
                    xblocks;

                xblocks = outlineOptions[category];
                if (!xblocks) {
                    return outline;
                }

                outline.child_info = childInfo; // eslint-disable-line no-param-reassign
                _.each(_.range(xblocks), function(xblockIndex) {
                    childInfo.children.push(
                        createChildXBlockInfo(category, outlineOptions, xblockIndex)
                    );
                });
                return outline;
            };

            /**
             * Create course outline.
             *
             * @param {Object} outlineOptions   options according to which outline was created
             * @returns {Object}
             */
            createCourseOutline = function(outlineOptions) {
                var courseXBlockInfo = {
                    category: 'course',
                    display_name: 'Demo Course',
                    id: 'COURSE_ID_101'
                };
                return createXBlockInfo('section', outlineOptions, courseXBlockInfo);
            };

            /**
             * Render breadcrumb and XBlock list view.
             *
             * @param {any} courseOutlineInfo      course outline info
             * @param {any} ancestorInfo           ancestors info
             */
            renderViews = function(courseOutlineInfo, ancestorInfo) {
                var ancestorInfo = ancestorInfo || {ancestors: []};  // eslint-disable-line no-redeclare
                modal.renderViews(courseOutlineInfo, ancestorInfo);
            };

            /**
             * Extract displayed XBlock list info.
             *
             * @returns {Object}
             */
            getDisplayedInfo = function() {
                var viewEl = modal.moveXBlockListView.$el;
                return {
                    categoryText: viewEl.find('.category-text').text().trim(),
                    currentLocationText: viewEl.find('.current-location').text().trim(),
                    xblockCount: viewEl.find('.xblock-item').length,
                    xblockDisplayNames: viewEl.find('.xblock-item .xblock-displayname').map(
                        function() { return $(this).text().trim(); }
                    ).get(),
                    forwardButtonSRTexts: viewEl.find('.xblock-item .forward-sr-text').map(
                        function() { return $(this).text().trim(); }
                    ).get(),
                    forwardButtonCount: viewEl.find('.fa-arrow-right.forward-sr-icon').length
                };
            };

            /**
             * Verify displayed XBlock list info.
             *
             * @param {String} category                 XBlock category
             * @param {Integer} expectedXBlocksCount    number of XBlock childs displayed
             * @param {Boolean} hasCurrentLocation      do we need to check current location
             */
            verifyListViewInfo = function(category, expectedXBlocksCount, hasCurrentLocation) {
                var displayedInfo = getDisplayedInfo();
                expect(displayedInfo.categoryText).toEqual(modal.moveXBlockListView.categoriesText[category] + ':');
                expect(displayedInfo.xblockCount).toEqual(expectedXBlocksCount);
                expect(displayedInfo.xblockDisplayNames).toEqual(
                    _.map(_.range(expectedXBlocksCount), function(xblockIndex) {
                        return category + '_display_name_' + xblockIndex;
                    })
                );
                if (category !== 'component') {
                    if (hasCurrentLocation) {
                        expect(displayedInfo.currentLocationText).toEqual('(Current location)');
                    }
                    expect(displayedInfo.forwardButtonSRTexts).toEqual(
                        _.map(_.range(expectedXBlocksCount), function() {
                            return 'Click for children';
                        })
                    );
                    expect(displayedInfo.forwardButtonCount).toEqual(expectedXBlocksCount);
                }
            };

            /**
             * Verify rendered breadcrumb info.
             *
             * @param {any} category        XBlock category
             * @param {any} xblockIndex     XBlock index
             */
            verifyBreadcrumbViewInfo = function(category, xblockIndex) {
                var displayedBreadcrumbs = modal.moveXBlockBreadcrumbView.$el.find('.breadcrumbs .bc-container').map(
                    function() { return $(this).text().trim(); }
                ).get(),
                    categories = _.keys(parentChildMap).concat(['component']),
                    visitedCategories = categories.slice(0, _.indexOf(categories, category));

                expect(displayedBreadcrumbs).toEqual(
                    _.map(visitedCategories, function(visitedCategory) {
                        return visitedCategory === 'course' ?
                            'Course Outline' : visitedCategory + '_display_name_' + xblockIndex;
                    })
                );
            };

            /**
             * Click forward button in the list of displayed XBlocks.
             *
             * @param {any} buttonIndex     forward button index
             */
            clickForwardButton = function(buttonIndex) {
                buttonIndex = buttonIndex || 0;  // eslint-disable-line no-param-reassign
                modal.moveXBlockListView.$el.find('[data-item-index="' + buttonIndex + '"] button').click();
            };

            /**
             * Click on last clickable breadcrumb button.
             */
            clickBreadcrumbButton = function() {
                modal.moveXBlockBreadcrumbView.$el.find('.bc-container button').last().click();
            };

            /**
             * Returns the parent or child category of current XBlock.
             *
             * @param {String} direction    `forward` or `backward`
             * @param {String} category     XBlock category
             * @returns {String}
             */
            nextCategory = function(direction, category) {
                return direction === 'forward' ? parentChildMap[category] : _.invert(parentChildMap)[category];
            };

            /**
             * Verify renderd info of breadcrumbs and XBlock list.
             *
             * @param {Object} outlineOptions       options according to which outline was created
             * @param {String} category             XBlock category
             * @param {Integer} buttonIndex         forward button index
             * @param {String} direction            `forward` or `backward`
             * @param {String} hasCurrentLocation   do we need to check current location
             * @returns
             */
            verifyXBlockInfo = function(outlineOptions, category, buttonIndex, direction, hasCurrentLocation) {
                var expectedXBlocksCount = outlineOptions[category];

                verifyListViewInfo(category, expectedXBlocksCount, hasCurrentLocation);
                verifyBreadcrumbViewInfo(category, buttonIndex);
                verifyMoveEnabled(category, hasCurrentLocation);

                if (direction === 'forward') {
                    if (category === 'component') {
                        return;
                    }
                    clickForwardButton(buttonIndex);
                } else if (direction === 'backward') {
                    if (category === 'section') {
                        return;
                    }
                    clickBreadcrumbButton();
                }
                category = nextCategory(direction, category);  // eslint-disable-line no-param-reassign

                verifyXBlockInfo(outlineOptions, category, buttonIndex, direction, hasCurrentLocation);
            };

            /**
             * Verify move button is enabled.
             *
             * @param {String} category             XBlock category
             * @param {String} hasCurrentLocation   do we need to check current location
             */
            verifyMoveEnabled = function(category, hasCurrentLocation) {
                var isMoveEnabled = !modal.$el.find('.modal-actions .action-move').hasClass('is-disabled');
                if (category === 'component' && !hasCurrentLocation) {
                    expect(isMoveEnabled).toBeTruthy();
                } else {
                    expect(isMoveEnabled).toBeFalsy();
                }
            };

            /**
             * Verify notification status.
             *
             * @param {Object} requests             requests object
             * @param {Object} notificationSpy      notification spy
             * @param {String} notificationText     notification text to be verified
             * @param {Integer} sourceIndex         source index of the xblock
             */
            verifyNotificationStatus = function(requests, notificationSpy, notificationText, sourceIndex) {
                var sourceIndex = sourceIndex || 0;  // eslint-disable-line no-redeclare
                ViewHelpers.verifyNotificationShowing(notificationSpy, notificationText);
                AjaxHelpers.respondWithJson(requests, {
                    move_source_locator: sourceLocator,
                    parent_locator: sourceParentLocator,
                    target_index: sourceIndex
                });
                ViewHelpers.verifyNotificationHidden(notificationSpy);
            };

            /**
             * Send move xblock request.
             *
             * @param {Object} requests             requests object
             * @param {Object} xblockLocator        Xblock id location
             * @param {Integer} targetIndex         target index of the xblock
             * @param {Integer} sourceIndex         source index of the xblock
             */
            sendMoveXBlockRequest = function(requests, xblockLocator, targetIndex, sourceIndex) {
                var responseData,
                    expectedData,
                    sourceIndex = sourceIndex || 0; // eslint-disable-line no-redeclare

                responseData = expectedData = {
                    move_source_locator: xblockLocator,
                    parent_locator: modal.targetParentXBlockInfo.id
                };

                if (targetIndex !== undefined) {
                    expectedData = _.extend(expectedData, {
                        targetIndex: targetIndex
                    });
                }

                // verify content of request
                AjaxHelpers.expectJsonRequest(requests, 'PATCH', '/xblock/', expectedData);

                // send the response
                AjaxHelpers.respondWithJson(requests, _.extend(responseData, {
                    source_index: sourceIndex
                }));
            };

            /**
             * Move xblock with success.
             *
             * @param {Object} requests             requests object
             */
            moveXBlockWithSuccess = function(requests) {
                // select a target item and click
                renderViews(courseOutline);
                _.each(_.range(3), function() {
                    clickForwardButton(1);
                });
                modal.$el.find('.modal-actions .action-move').click();
                sendMoveXBlockRequest(requests, sourceLocator);
                expect(modal.movedAlertView).toBeDefined();
                verifyConfirmationFeedbackTitleHtml(sourceDisplayName);
                verifyConfirmationFeedbackRedirectLinkHtml();
                verifyConfirmationFeedbackUndoMoveActionHtml();
            };

            /**
             * Verify success banner message html has correct title html.
             *
             * @param {String} displayName             XBlock display name
             */
            verifyConfirmationFeedbackTitleHtml = function(displayName) {
                expect(modal.movedAlertView.$el.find('.title').html().trim())
                .toEqual(StringUtils.interpolate('Success! "{displayName}" has been moved.',
                    {
                        displayName: displayName
                    })
                );
            };

            /**
             * Verify undo success banner message html has correct title html.
             *
             * @param {String} displayName             XBlock display name
             */
            verifyUndoConfirmationFeedbackTitleHtml = function(displayName) {
                expect(modal.movedAlertView.$el.find('.title').html()).toEqual(
                    StringUtils.interpolate(
                        'Move cancelled. "{sourceDisplayName}" has been moved back to its original location.',
                        {
                            sourceDisplayName: displayName
                        }
                    )
                );
            };

            /**
             * Verify success banner message html has correct redirect link html.
             */
            verifyConfirmationFeedbackRedirectLinkHtml = function() {
                expect(modal.movedAlertView.$el.find('.copy').html().indexOf(
                    HtmlUtils.HTML(
                        '<button class="action-secondary action-cancel">Take me to the new location</button>'
                    ) !== -1
                )).toBeTruthy();
            };

            /**
             * Verify success banner message html has correct undo move button html.
             */
            verifyConfirmationFeedbackUndoMoveActionHtml = function() {
                expect(modal.movedAlertView.$el.find('.copy').html().indexOf(
                    HtmlUtils.HTML(
                        '<button class="action-primary action-save">Undo Move</button>'
                    ) !== -1
                )).toBeTruthy();
            };

            /**
             * Get sent requests.
             *
             * @returns {Object}
             */
            getSentRequests = function() {
                return jasmine.Ajax.requests.filter(function(request) {
                    return request.readyState > 0;
                });
            };

            it('renders views with correct information', function() {
                var outlineOptions = {section: 1, subsection: 1, unit: 1, component: 1},
                    outline = createCourseOutline(outlineOptions);

                renderViews(outline, xblockAncestorInfo);
                verifyXBlockInfo(outlineOptions, 'section', 0, 'forward', true);
                verifyXBlockInfo(outlineOptions, 'component', 0, 'backward', true);
            });

            it('shows correct behavior on breadcrumb navigation', function() {
                var outline = createCourseOutline({section: 1, subsection: 1, unit: 1, component: 1});

                renderViews(outline);
                _.each(_.range(3), function() {
                    clickForwardButton();
                });

                _.each(['component', 'unit', 'subsection', 'section'], function(category) {
                    verifyListViewInfo(category, 1);
                    if (category !== 'section') {
                        modal.moveXBlockBreadcrumbView.$el.find('.bc-container button').last().click();
                    }
                });
            });

            it('shows the correct current location', function() {
                var outlineOptions = {section: 2, subsection: 2, unit: 2, component: 2},
                    outline = createCourseOutline(outlineOptions);
                renderViews(outline, xblockAncestorInfo);
                verifyXBlockInfo(outlineOptions, 'section', 0, 'forward', true);
                // click the outline breadcrumb to render sections
                modal.moveXBlockBreadcrumbView.$el.find('.bc-container button').first().click();
                verifyXBlockInfo(outlineOptions, 'section', 1, 'forward', false);
            });

            it('shows correct message when parent has no children', function() {
                var outlinesInfo = [
                    {
                        outline: createCourseOutline({}),
                        message: 'This course has no sections'
                    },
                    {
                        outline: createCourseOutline({section: 1}),
                        message: 'This section has no subsections',
                        forwardClicks: 1
                    },
                    {
                        outline: createCourseOutline({section: 1, subsection: 1}),
                        message: 'This subsection has no units',
                        forwardClicks: 2
                    },
                    {
                        outline: createCourseOutline({section: 1, subsection: 1, unit: 1}),
                        message: 'This unit has no components',
                        forwardClicks: 3
                    }
                ];

                _.each(outlinesInfo, function(info) {
                    renderViews(info.outline);
                    _.each(_.range(info.forwardClicks), function() {
                        clickForwardButton();
                    });
                    expect(modal.moveXBlockListView.$el.find('.xblock-no-child-message').text().trim())
                        .toEqual(info.message);
                    modal.moveXBlockListView.undelegateEvents();
                    modal.moveXBlockBreadcrumbView.undelegateEvents();
                });
            });

            describe('Move an xblock', function() {
                it('can not move in a disabled state', function() {
                    verifyMoveEnabled(false);
                    modal.$el.find('.modal-actions .action-move').click();
                    expect(modal.movedAlertView).toBeNull();
                    expect(getSentRequests().length).toEqual(0);
                });

                it('move button is disabled when navigating to same parent', function() {
                    // select a target parent as the same as source parent and click
                    renderViews(courseOutline);
                    _.each(_.range(3), function() {
                        clickForwardButton(0);
                    });
                    verifyMoveEnabled('component', true);
                });

                it('move button is enabled when navigating to different parent', function() {
                    // select a target parent as the different as source parent and click
                    renderViews(courseOutline);
                    _.each(_.range(3), function() {
                        clickForwardButton(1);
                    });
                    verifyMoveEnabled('component', false);
                });

                it('verify move state while navigating', function() {
                    renderViews(courseOutline, xblockAncestorInfo);
                    verifyXBlockInfo(courseOutlineOptions, 'section', 0, 'forward', true);
                    // start from course outline again
                    modal.moveXBlockBreadcrumbView.$el.find('.bc-container button').first().click();
                    verifyXBlockInfo(courseOutlineOptions, 'section', 1, 'forward', false);
                });

                it('move an xblock when move button is clicked', function() {
                    var requests = AjaxHelpers.requests(this);
                    moveXBlockWithSuccess(requests);
                });

                it('do not move an xblock when cancel button is clicked', function() {
                    modal.$el.find('.modal-actions .action-cancel').click();
                    expect(modal.movedAlertView).toBeNull();
                    expect(getSentRequests().length).toEqual(0);
                });

                it('undo move an xblock when undo move link is clicked', function() {
                    var sourceIndex = 0,
                        requests = AjaxHelpers.requests(this);
                    moveXBlockWithSuccess(requests);
                    modal.movedAlertView.$el.find('.action-save').click();
                    AjaxHelpers.respondWithJson(requests, {
                        move_source_locator: sourceLocator,
                        parent_locator: sourceParentLocator,
                        target_index: sourceIndex
                    });
                    verifyUndoConfirmationFeedbackTitleHtml(sourceDisplayName);
                });
            });

            describe('shows a notification', function() {
                it('mini operation message when moving an xblock', function() {
                    var requests = AjaxHelpers.requests(this),
                        notificationSpy = ViewHelpers.createNotificationSpy();
                    // navigate to a target parent and click
                    renderViews(courseOutline);
                    _.each(_.range(3), function() {
                        clickForwardButton(1);
                    });
                    modal.$el.find('.modal-actions .action-move').click();
                    verifyNotificationStatus(requests, notificationSpy, 'Moving');
                });

                it('mini operation message when undo moving an xblock', function() {
                    var notificationSpy,
                        requests = AjaxHelpers.requests(this);
                    moveXBlockWithSuccess(requests);
                    notificationSpy = ViewHelpers.createNotificationSpy();
                    modal.movedAlertView.$el.find('.action-save').click();
                    verifyNotificationStatus(requests, notificationSpy, 'Undo moving');
                });

                it('error message when move request fails', function() {
                    var requests = AjaxHelpers.requests(this),
                        notificationSpy = ViewHelpers.createNotificationSpy('Error');
                    // select a target item and click
                    renderViews(courseOutline);
                    _.each(_.range(3), function() {
                        clickForwardButton(1);
                    });
                    modal.$el.find('.modal-actions .action-move').click();
                    AjaxHelpers.respondWithError(requests);
                    ViewHelpers.verifyNotificationShowing(notificationSpy, "Studio's having trouble saving your work");
                });

                it('error message when undo move request fails', function() {
                    var requests = AjaxHelpers.requests(this),
                        notificationSpy = ViewHelpers.createNotificationSpy('Error');
                    moveXBlockWithSuccess(requests);
                    modal.movedAlertView.$el.find('.action-save').click();
                    AjaxHelpers.respondWithError(requests);
                    ViewHelpers.verifyNotificationShowing(notificationSpy, "Studio's having trouble saving your work");
                });
            });
        });
    });
