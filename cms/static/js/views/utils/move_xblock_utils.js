/**
 * Provides utilities for move xblock.
 */
define([
    'jquery',
    'underscore',
    'common/js/components/views/feedback',
    'common/js/components/views/feedback_alert',
    'js/views/utils/xblock_utils',
    'js/views/utils/move_xblock_utils',
    'edx-ui-toolkit/js/utils/string-utils'
],
function($, _, Feedback, AlertView, XBlockViewUtils, MoveXBlockUtils, StringUtils) {
    'use strict';
    var redirectLink, undoMoveXBlock, showMovedNotification, hideMovedNotification;

    redirectLink = function(link) {
        window.location.href = link;
    };

    undoMoveXBlock = function(data) {
        XBlockViewUtils.moveXBlock(data.sourceLocator, data.sourceParentLocator, data.targetIndex)
        .done(function(response) {
            // show XBlock element
            $('.studio-xblock-wrapper[data-locator="' + response.move_source_locator + '"]').show();
            showMovedNotification(
                StringUtils.interpolate(
                    gettext('Move cancelled. "{sourceDisplayName}" has been moved back to its original location.'),
                    {
                        sourceDisplayName: data.sourceDisplayName
                    }
                )
            );
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
                        data: JSON.stringify({
                            sourceDisplayName: data.sourceDisplayName,
                            sourceLocator: data.sourceLocator,
                            sourceParentLocator: data.sourceParentLocator,
                            targetIndex: data.targetIndex
                        }),
                        click: function() {
                            undoMoveXBlock(
                                {
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
                            data: JSON.stringify({
                                targetParentLocator: data.targetParentLocator
                            }),
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
        showMovedNotification: showMovedNotification,
        hideMovedNotification: hideMovedNotification
    };
});
