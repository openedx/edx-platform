/**
 * Provides utilities for move xblock.
 */
define([
    'jquery',
    'underscore',
    'backbone',
    'common/js/components/views/feedback',
    'common/js/components/views/feedback_alert',
    'js/views/utils/xblock_utils',
    'js/views/utils/move_xblock_utils',
    'edx-ui-toolkit/js/utils/string-utils',
    'jquery.smoothScroll'
],
function($, _, Backbone, Feedback, AlertView, XBlockViewUtils, MoveXBlockUtils, StringUtils) {
    'use strict';
    var redirectLink, moveXBlock, undoMoveXBlock, showMovedNotification, hideMovedNotification;

    redirectLink = function(link) {
        window.location.href = link;
    };

    moveXBlock = function(data) {
        XBlockViewUtils.moveXBlock(data.sourceLocator, data.targetParentLocator)
            .done(function(response) {
            // hide modal
                Backbone.trigger('move:hideMoveModal');
                // hide xblock element
                data.sourceXBlockElement.hide();
                showMovedNotification(
                    StringUtils.interpolate(
                        gettext('Success! "{displayName}" has been moved.'),
                        {
                            displayName: data.sourceDisplayName
                        }
                    ),
                    {
                        sourceXBlockElement: data.sourceXBlockElement,
                        sourceDisplayName: data.sourceDisplayName,
                        sourceLocator: data.sourceLocator,
                        sourceParentLocator: data.sourceParentLocator,
                        targetParentLocator: data.targetParentLocator,
                        targetIndex: response.source_index
                    }
                );
                Backbone.trigger('move:onXBlockMoved');
            });
    };

    undoMoveXBlock = function(data) {
        XBlockViewUtils.moveXBlock(data.sourceLocator, data.sourceParentLocator, data.targetIndex)
            .done(function() {
            // show XBlock element
                data.sourceXBlockElement.show();
                showMovedNotification(
                    StringUtils.interpolate(
                        gettext('Move cancelled. "{sourceDisplayName}" has been moved back to its original location.'),
                        {
                            sourceDisplayName: data.sourceDisplayName
                        }
                    )
                );
                Backbone.trigger('move:onXBlockMoved');
            });
    };

    showMovedNotification = function(title, data) {
        var movedAlertView;
        // data is provided when we click undo move button.
        if (data) {
            movedAlertView = new AlertView.Confirmation({
                title: title,
                actions: {
                    primary: {
                        text: gettext('Undo move'),
                        class: 'action-save',
                        click: function() {
                            undoMoveXBlock(
                                {
                                    sourceXBlockElement: data.sourceXBlockElement,
                                    sourceDisplayName: data.sourceDisplayName,
                                    sourceLocator: data.sourceLocator,
                                    sourceParentLocator: data.sourceParentLocator,
                                    targetIndex: data.targetIndex
                                }
                            );
                        }
                    },
                    secondary: [
                        {
                            text: gettext('Take me to the new location'),
                            class: 'action-cancel',
                            click: function() {
                                redirectLink('/container/' + data.targetParentLocator);
                            }
                        }
                    ]
                }
            });
        } else {
            movedAlertView = new AlertView.Confirmation({
                title: title
            });
        }
        movedAlertView.show();
        // scroll to top
        $.smoothScroll({
            offset: 0,
            easing: 'swing',
            speed: 1000
        });
        movedAlertView.$('.wrapper').first().focus();
        return movedAlertView;
    };

    hideMovedNotification = function() {
        var movedAlertView = Feedback.active_alert;
        if (movedAlertView) {
            AlertView.prototype.hide.apply(movedAlertView);
        }
    };

    return {
        redirectLink: redirectLink,
        moveXBlock: moveXBlock,
        undoMoveXBlock: undoMoveXBlock,
        showMovedNotification: showMovedNotification,
        hideMovedNotification: hideMovedNotification
    };
});
