define(['jquery', 'underscore', 'edx-ui-toolkit/js/utils/spec-helpers/ajax-helpers',
        'common/js/spec_helpers/template_helpers', 'common/js/spec_helpers/view_helpers',
        'js/views/modals/move_xblock_modal', 'edx-ui-toolkit/js/utils/html-utils',
        'edx-ui-toolkit/js/utils/string-utils', 'js/models/xblock_info'],
    function($, _, AjaxHelpers, TemplateHelpers, ViewHelpers, MoveXBlockModal, HtmlUtils, StringUtils, XBlockInfo) {
        'use strict';

        var modal,
            showModal,
            verifyNotificationStatus,
            getConfirmationFeedbackTitle,
            getUndoConfirmationFeedbackTitle,
            getConfirmationFeedbackTitleLink,
            getConfirmationFeedbackMessageLink,
            sourceDisplayName = 'HTML 101',
            outlineUrl = '/course/cid?formats=concise',
            sourceLocator = 'source-xblock-locator',
            targetParentLocator = 'target-parent-xblock-locator',
            sourceParentLocator = 'source-parent-xblock-locator';

        describe('MoveXBlockModal', function() {
            var modal,
                showModal,
                DISPLAY_NAME = 'HTML 101',
                OUTLINE_URL = '/course/cid?formats=concise';

            showModal = function() {
                modal = new MoveXBlockModal({
                    sourceXBlockInfo: new XBlockInfo({
                        id: 'testCourse/branch/draft/block/verticalFFF',
                        display_name: DISPLAY_NAME,
                        category: 'html'
                    }),
                    XBlockUrlRoot: '/xblock',
                    outlineURL: OUTLINE_URL
                });
                modal.show();
            };

            beforeEach(function() {
                TemplateHelpers.installTemplates([
                    'basic-modal',
                    'modal-button',
                    'move-xblock-modal'
                ]);
            });

            afterEach(function() {
                modal.hide();
            });

            it('rendered as expected', function() {
                showModal();
                expect(modal.$el.find('.modal-header .title').text()).toEqual('Move: ' + DISPLAY_NAME);
                expect(modal.$el.find('.modal-actions .action-primary.action-move').text()).toEqual('Move');
            });

            it('sends request to fetch course outline', function() {
                var requests = AjaxHelpers.requests(this),
                    renderViewsSpy;
                showModal();
                renderViewsSpy = spyOn(modal, 'renderViews');
                AjaxHelpers.expectRequest(requests, 'GET', OUTLINE_URL);
                AjaxHelpers.respondWithJson(requests, {});
                expect(renderViewsSpy).toHaveBeenCalled();
            });
        });

        describe('MoveXBlockModal', function() {
            beforeEach(function() {
                TemplateHelpers.installTemplates([
                    'basic-modal',
                    'modal-button',
                    'move-xblock-modal'
                ]);
                showModal();
            });

            it('rendered as expected', function() {
                expect(modal.$el.find('.modal-header .title').text()).toEqual('Move: ' + sourceDisplayName);
                expect(modal.$el.find('.modal-actions .action-primary.action-move').text()).toEqual('Move');
            });
        });

        showModal = function() {
            modal = new MoveXBlockModal({
                sourceXBlockInfo: new XBlockInfo({
                    id: sourceLocator,
                    display_name: sourceDisplayName,
                    category: 'html'
                }),
                sourceParentXBlockInfo: new XBlockInfo({
                    id: sourceParentLocator,
                    display_name: 'VERT 101',
                    category: 'vertical'
                }),
                XBlockUrlRoot: '/xblock',
                outlineURL: outlineUrl
            });
            modal.show();
        };

        getConfirmationFeedbackTitle = function(displayName) {
            return StringUtils.interpolate(
                gettext('Success! "{displayName}" has been moved to a new location.'),
                {
                    displayName: displayName
                }
            );
        };

        getUndoConfirmationFeedbackTitle = function(displayName) {
            return StringUtils.interpolate(
                gettext('Undo Success! "{sourceDisplayName}" has been moved back to a previous location.'),
                {
                    sourceDisplayName: displayName
                }
            );
        };

        getConfirmationFeedbackTitleLink = function(parentLocator) {
            return StringUtils.interpolate(
                gettext(' {link_start}Take me there{link_end}'),
                {
                    link_start: HtmlUtils.HTML('<a href="/container/' + parentLocator + '">'),
                    link_end: HtmlUtils.HTML('</a>')
                }
            );
        };

        getConfirmationFeedbackMessageLink = function(displayName, locator, parentLocator, sourceIndex) {
            return HtmlUtils.interpolateHtml(
                HtmlUtils.HTML(
                    '<a class="action-undo-move" href="#" data-source-display-name="{displayName}" ' +
                    'data-source-locator="{sourceLocator}" data-parent-locator="{parentLocator}" ' +
                    'data-target-index="{targetIndex}">{undoMove}</a>'),
                {
                    displayName: displayName,
                    sourceLocator: locator,
                    parentLocator: parentLocator,
                    targetIndex: sourceIndex,
                    undoMove: gettext('Undo move')
                }
            );
        };

        verifyNotificationStatus = function(requests, notificationSpy, notificationText, sourceIndex) {
            var sourceIndex = sourceIndex || 0;
            ViewHelpers.verifyNotificationShowing(notificationSpy, notificationText);
            AjaxHelpers.respondWithJson(requests, {
                move_source_locator: sourceLocator,
                parent_locator: sourceParentLocator,
                target_index: sourceIndex
            });
            ViewHelpers.verifyNotificationHidden(notificationSpy);
        };

        describe('Move an xblock', function() {
            var sendMoveXBlockRequest,
                moveXBlockWithSuccess;
            beforeEach(function() {
                TemplateHelpers.installTemplates([
                    'basic-modal',
                    'modal-button',
                    'move-xblock-modal'
                ]);
                showModal();
            });

            sendMoveXBlockRequest = function(requests, xblockLocator, parentLocator, targetIndex, sourceIndex) {
                var responseData,
                    expectData,
                    sourceIndex = sourceIndex || 0, // eslint-disable-line no-redeclare
                    moveButton = modal.$el.find('.modal-actions .action-move')[sourceIndex];

                // select a target item and click
                modal.targetParentXBlockInfo = {
                    id: parentLocator
                };
                moveButton.click();

                responseData = expectData = {
                    move_source_locator: xblockLocator,
                    parent_locator: parentLocator
                };

                if (targetIndex !== undefined) {
                    expectData = _.extend(expectData, {
                        targetIndex: targetIndex
                    });
                }

                // verify content of request
                AjaxHelpers.expectJsonRequest(requests, 'PATCH', '/xblock/', expectData);

                // send the response
                AjaxHelpers.respondWithJson(requests, _.extend(responseData, {
                    source_index: sourceIndex
                }));
            };

            moveXBlockWithSuccess = function(requests) {
                var sourceIndex = 0;
                sendMoveXBlockRequest(requests, sourceLocator, targetParentLocator);
                expect(modal.movedAlertView).toBeDefined();
                expect(modal.movedAlertView.options.title).toEqual(getConfirmationFeedbackTitle(sourceDisplayName));
                expect(modal.movedAlertView.options.titleLink).toEqual(
                    getConfirmationFeedbackTitleLink(targetParentLocator)
                );
                expect(modal.movedAlertView.options.messageLink).toEqual(
                    getConfirmationFeedbackMessageLink(
                        sourceDisplayName,
                        sourceLocator,
                        sourceParentLocator,
                        sourceIndex
                    )
                );
            };

            it('moves an xblock when move button is clicked', function() {
                var requests = AjaxHelpers.requests(this);
                moveXBlockWithSuccess(requests);
            });

            it('undo move an xblock when undo move button is clicked', function() {
                var sourceIndex = 0,
                    requests = AjaxHelpers.requests(this);
                moveXBlockWithSuccess(requests);
                modal.movedAlertView.undoMoveXBlock({
                    target: $(modal.movedAlertView.options.messageLink.text)
                });
                AjaxHelpers.respondWithJson(requests, {
                    move_source_locator: sourceLocator,
                    parent_locator: sourceParentLocator,
                    target_index: sourceIndex
                });
                expect(modal.movedAlertView.movedAlertView.options.title).toEqual(
                    getUndoConfirmationFeedbackTitle(sourceDisplayName)
                );
            });

            it('does not move an xblock when cancel button is clicked', function() {
                var sourceIndex = 0;
                // select a target parent and click cancel button
                modal.targetParentXBlockInfo = {
                    id: sourceParentLocator
                };
                modal.$el.find('.modal-actions .action-cancel')[sourceIndex].click();
                expect(modal.movedAlertView).toBeNull();
            });

            it('shows a notification when moving', function() {
                var requests = AjaxHelpers.requests(this),
                    notificationSpy = ViewHelpers.createNotificationSpy();
                // select a target item and click on move
                modal.targetParentXBlockInfo = {
                    id: targetParentLocator
                };
                modal.$el.find('.modal-actions .action-move').click();
                verifyNotificationStatus(requests, notificationSpy, 'Moving');
            });

            it('shows a notification when undo moving', function() {
                var notificationSpy,
                    requests = AjaxHelpers.requests(this);
                moveXBlockWithSuccess(requests);
                notificationSpy = ViewHelpers.createNotificationSpy();
                modal.movedAlertView.undoMoveXBlock({
                    target: $(modal.movedAlertView.options.messageLink.text)
                });
                verifyNotificationStatus(requests, notificationSpy, 'Undo moving');
            });
        });
    });
