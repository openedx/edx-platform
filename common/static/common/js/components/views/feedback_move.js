/**
 * The MovedAlertView to show confirmation message when moving XBlocks.
 */
(function(define) {
    'use strict';
    define(['jquery', 'underscore', 'common/js/components/views/feedback_alert', 'js/views/utils/xblock_utils',
        'js/views/utils/move_xblock_utils', 'edx-ui-toolkit/js/utils/string-utils'],
        function($, _, AlertView, XBlockViewUtils, MoveXBlockUtils, StringUtils) {
            var MovedAlertView = AlertView.Confirmation.extend({
                events: _.extend({}, AlertView.Confirmation.prototype.events, {
                    'click .action-undo-move': 'undoMoveXBlock'
                }),

                options: $.extend({}, AlertView.Confirmation.prototype.options),

                initialize: function() {
                    AlertView.prototype.initialize.apply(this, arguments);
                    this.movedAlertView = null;
                },

                undoMoveXBlock: function(event) {
                    var self = this,
                        $moveButton = $(event.target),
                        sourceLocator = $moveButton.data('source-locator'),
                        sourceDisplayName = $moveButton.data('source-display-name'),
                        sourceParentLocator = $moveButton.data('source-parent-locator'),
                        targetIndex = $moveButton.data('target-index');
                    XBlockViewUtils.moveXBlock(sourceLocator, sourceParentLocator, targetIndex)
                    .done(function(response) {
                        // show XBlock element
                        $('.studio-xblock-wrapper[data-locator="' + response.move_source_locator + '"]').show();
                        if (self.movedAlertView) {
                            self.movedAlertView.hide();
                        }
                        self.movedAlertView = MoveXBlockUtils.showMovedNotification(
                            StringUtils.interpolate(
                                gettext('Move cancelled. "{sourceDisplayName}" has been moved back to its original ' +
                                    'location.'),
                                {
                                    sourceDisplayName: sourceDisplayName
                                }
                            )
                        );
                    });
                }
            });
            return MovedAlertView;
        });
}).call(this, define || RequireJS.define);
