/**
 * The MovedAlertView to show confirmation message when moving XBlocks in course.
 */
(function(define) {
    'use strict';
    define(['jquery', 'underscore', 'underscore.string', 'common/js/components/views/feedback_alert',
    'js/views/utils/xblock_utils', 'edx-ui-toolkit/js/utils/string-utils'],
        function($, _, str, AlertView, XBlockViewUtils, StringUtils) {
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
                        $moveLink = $(event.target),
                        sourceLocator = $moveLink.data('source-locator'),
                        sourceDisplayName = $moveLink.data('source-display-name'),
                        parentLocator = $moveLink.data('parent-locator'),
                        targetIndex = $moveLink.data('target-index');
                    XBlockViewUtils.moveXBlock(sourceLocator, parentLocator, targetIndex)
                    .done(function(response) {
                        // show XBlock element
                        $('.studio-xblock-wrapper[data-locator="' + response.move_source_locator + '"]').show();
                        if (self.movedAlertView) {
                            self.movedAlertView.hide();
                        }
                        self.movedAlertView = new MovedAlertView({
                            title: StringUtils.interpolate(
                                gettext(
                                    'Undo Success! "{sourceDisplayName}" has been moved back to a previous location.'
                                ), {
                                    sourceDisplayName: sourceDisplayName
                                }
                            ),
                            maxShown: 10000
                        });
                        self.movedAlertView.show();
                        // scroll to top
                        $.smoothScroll({
                            offset: 0,
                            easing: 'swing',
                            speed: 1000
                        });
                    });
                }
            });
            return MovedAlertView;
        });
}).call(this, define || RequireJS.define);
