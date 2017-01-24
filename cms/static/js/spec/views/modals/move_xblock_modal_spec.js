define(['jquery', 'underscore', 'edx-ui-toolkit/js/utils/spec-helpers/ajax-helpers',
        'common/js/spec_helpers/template_helpers', 'common/js/spec_helpers/view_helpers',
        'js/views/modals/move_xblock_modal', 'edx-ui-toolkit/js/utils/html-utils',
        'edx-ui-toolkit/js/utils/string-utils', 'js/models/xblock_info'],
    function($, _, AjaxHelpers, TemplateHelpers, ViewHelpers, MoveXBlockModal, HtmlUtils, StringUtils, XBlockInfo) {
        'use strict';

        var modal,
            showModal,
            verifyNotificationStatus,
            isMoveEnabled,
            enableMove,
            selectTargetParent,
            getConfirmationFeedbackTitle,
            getUndoConfirmationFeedbackTitle,
            getConfirmationFeedbackTitleHtml,
            getConfirmationFeedbackMessageHtml,
            sourceDisplayName = 'HTML 101',
            outlineUrl = '/course/cid?formats=concise',
            sourceLocator = 'source-xblock-locator',
            targetParentLocator = 'target-parent-xblock-locator',
            sourceParentLocator = 'source-parent-xblock-locator';

        describe('MoveXBlockModal', function() {
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
                expect(modal.$el.find('.modal-header .title').text()).toEqual('Move: ' + sourceDisplayName);
                expect(modal.$el.find('.modal-actions .action-primary.action-move').text()).toEqual('Move');
            });

            it('sends request to fetch course outline', function() {
                var requests = AjaxHelpers.requests(this),
                    renderViewsSpy;
                showModal();
                renderViewsSpy = spyOn(modal, 'renderViews');
                AjaxHelpers.expectRequest(requests, 'GET', outlineUrl);
                AjaxHelpers.respondWithJson(requests, {});
                expect(renderViewsSpy).toHaveBeenCalled();
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

        isMoveEnabled = function(sourceIndex) {
            var moveButton = modal.$el.find('.modal-actions .action-move')[sourceIndex];
            return !$(moveButton).hasClass('is-disabled');
        };

        enableMove = function(sourceIndex) {
            var moveButton = modal.$el.find('.modal-actions .action-move')[sourceIndex];
            $(moveButton).removeClass('is-disabled');
        };

        selectTargetParent = function(parentLocator) {
            modal.moveXBlockListView = {
                parent_info: {
                    parent: {
                        id: parentLocator
                    }
                },
                remove: function() {}   // attach a fake remove method
            };
        };

        getConfirmationFeedbackTitle = function(displayName) {
            return StringUtils.interpolate(
                'Success! "{displayName}" has been moved.',
                {
                    displayName: displayName
                }
            );
        };

        getUndoConfirmationFeedbackTitle = function(displayName) {
            return StringUtils.interpolate(
                'Move cancelled. "{sourceDisplayName}" has been moved back to its original location.',
                {
                    sourceDisplayName: displayName
                }
            );
        };

        getConfirmationFeedbackTitleHtml = function(parentLocator) {
            return StringUtils.interpolate(
                '{link_start}Take me to the new location{link_end}',
                {
                    link_start: HtmlUtils.HTML('<a href="/container/' + parentLocator + '">'),
                    link_end: HtmlUtils.HTML('</a>')
                }
            );
        };

        getConfirmationFeedbackMessageHtml = function(displayName, locator, parentLocator, sourceIndex) {
            return HtmlUtils.interpolateHtml(
                HtmlUtils.HTML(
                    '<a class="action-undo-move" href="#" data-source-display-name="{displayName}" ' +
                    'data-source-locator="{sourceLocator}" data-source-parent-locator="{parentSourceLocator}" ' +
                    'data-target-index="{targetIndex}">{undoMove}</a>'),
                {
                    displayName: displayName,
                    sourceLocator: locator,
                    parentSourceLocator: parentLocator,
                    targetIndex: sourceIndex,
                    undoMove: gettext('Undo move')
                }
            );
        };

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

            afterEach(function() {
                modal.hide();
            });

            sendMoveXBlockRequest = function(requests, xblockLocator, parentLocator, targetIndex, sourceIndex) {
                var responseData,
                    expectedData,
                    sourceIndex = sourceIndex || 0, // eslint-disable-line no-redeclare
                    moveButton = modal.$el.find('.modal-actions .action-move')[sourceIndex];

                if(isMoveEnabled(sourceIndex)) {
                    // select a target item and click
                    selectTargetParent(parentLocator);
                    moveButton.click();

                    responseData = expectedData = {
                        move_source_locator: xblockLocator,
                        parent_locator: parentLocator
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
                }
            };

            moveXBlockWithSuccess = function(requests) {
                var sourceIndex = 0;
                enableMove(sourceIndex);
                sendMoveXBlockRequest(requests, sourceLocator, targetParentLocator);
                expect(modal.movedAlertView).toBeDefined();
                expect(modal.movedAlertView.options.title).toEqual(getConfirmationFeedbackTitle(sourceDisplayName));
                expect(modal.movedAlertView.options.titleHtml).toEqual(
                    getConfirmationFeedbackTitleHtml(targetParentLocator)
                );
                expect(modal.movedAlertView.options.messageHtml).toEqual(
                    getConfirmationFeedbackMessageHtml(
                        sourceDisplayName,
                        sourceLocator,
                        sourceParentLocator,
                        sourceIndex
                    )
                );
            };

            it('disabled by default', function() {
                expect(isMoveEnabled(0)).toBeFalsy();
            });

            it('can not move is disabled state', function() {
                var requests = AjaxHelpers.requests(this);
                expect(isMoveEnabled(0)).toBeFalsy();
                sendMoveXBlockRequest(requests, sourceLocator, targetParentLocator);
                expect(modal.movedAlertView).toBeNull();
            });

            it('moves an xblock when move button is clicked', function() {
                var requests = AjaxHelpers.requests(this);
                moveXBlockWithSuccess(requests);
            });

            it('undo move an xblock when undo move button is clicked', function() {
                var sourceIndex = 0,
                    requests = AjaxHelpers.requests(this);
                moveXBlockWithSuccess(requests);
                modal.movedAlertView.undoMoveXBlock({
                    target: $(modal.movedAlertView.options.messageHtml.text)
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
                selectTargetParent(targetParentLocator);
                modal.$el.find('.modal-actions .action-cancel')[sourceIndex].click();
                expect(modal.movedAlertView).toBeNull();
            });

            it('shows a notification when moving', function() {
                var requests = AjaxHelpers.requests(this),
                    notificationSpy = ViewHelpers.createNotificationSpy();
                // select a target item and click on move
                selectTargetParent(targetParentLocator);
                modal.$el.find('.modal-actions .action-move').click();
                verifyNotificationStatus(requests, notificationSpy, 'Moving');
            });

            it('shows a notification when undo moving', function() {
                var notificationSpy,
                    requests = AjaxHelpers.requests(this);
                moveXBlockWithSuccess(requests);
                notificationSpy = ViewHelpers.createNotificationSpy();
                modal.movedAlertView.undoMoveXBlock({
                    target: $(modal.movedAlertView.options.messageHtml.text)
                });
                verifyNotificationStatus(requests, notificationSpy, 'Undo moving');
            });
        });
    });
