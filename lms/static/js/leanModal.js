(function($) {  // eslint-disable-line wrap-iife
    'use strict';
    $.fn.extend({
        /*
         * leanModal prepares an element to be a modal dialog.  Call it once on the
         * element that launches the dialog, when the page is ready.  This function
         * will add a .click() handler that properly opens the dialog.
         *
         * The launching element must:
         *   - be an <a> element, not a button,
         *   - have an href= attribute identifying the id of the dialog element,
         *   - have rel='leanModal'.
         */
        leanModal: function(options) {
            var defaults = {
                top: 100,
                overlay: 0.5,
                closeButton: null,
                position: 'fixed'
            };
            var overlay = '<div id="lean_overlay"></div>';
            if ($('#lean_overlay').length === 0) {
                edx.HtmlUtils.append(
                    $('body'),
                    $(overlay)
                );
            }

            options = $.extend(defaults, options);  // eslint-disable-line no-param-reassign

            function closeModal(modalId, e) {
                $('#lean_overlay').fadeOut(200);
                $('iframe', modalId).attr('src', '');
                $(modalId).css({display: 'none'});
                if (modalId === '#modal_clone') {
                    $(modalId).remove();
                }
                e.preventDefault();
                $(document).off('keydown.leanModal');
            }

            return this.each(function() {
                var o = options;

                $(this).click(function(e) {
                    var modalId = $(this).attr('href'),
                        modalClone, modalCloneHtml, notice, $notice;

                    $('.modal').hide();

                    if ($(modalId).hasClass('video-modal')) {
                        // Video modals need to be cloned before being presented as a modal
                        // This is because actions on the video get recorded in the history.
                        // Deleting the video (clone) prevents the odd back button behavior.
                        modalClone = $(modalId).clone(true, true);
                        modalClone.attr('id', 'modal_clone');
                        modalCloneHtml = edx.HtmlUtils.template(modalClone);
                        $(modalId).after(
                            edx.HtmlUtils.ensureHtml(modalCloneHtml).toString()
                        );
                        modalId = '#modal_clone';
                    }

                    $(document).on('keydown.leanModal', function(event) {
                        if (event.which === 27) {
                            closeModal(modalId, event);
                        }
                    });

                    $('#lean_overlay').click(function(ev) {
                        closeModal(modalId, ev);
                    });

                    $(o.closeButton).click(function(ev) {
                        closeModal(modalId, ev);
                    });

                    // To enable closing of email modal when copy button hit
                    $(o.copyEmailButton).click(function(ev) {
                        closeModal(modalId, ev);
                    });

                    $('#lean_overlay').css({display: 'block', opacity: 0});
                    $('#lean_overlay').fadeTo(200, o.overlay);

                    $('iframe', modalId).attr('src', $('iframe', modalId).data('src'));
                    if ($(modalId).hasClass('email-modal')) {
                        $(modalId).css({
                            width: 80 + '%',
                            height: 80 + '%',
                            position: o.position,
                            opacity: 0,
                            'z-index': 11000,
                            left: 10 + '%',
                            top: 10 + '%'
                        });
                    } else {
                        $(modalId).css({
                            position: o.position,
                            opacity: 0,
                            'z-index': 11000,
                            left: 50 + '%',
                            'margin-left': -($(modalId).outerWidth() / 2) + 'px',
                            top: o.top + 'px'
                        });
                    }

                    $(modalId).show().fadeTo(200, 1);
                    $(modalId).find('.notice').hide()
                                              .html('');
                    notice = $(this).data('notice');
                    if (notice !== undefined) {
                        $notice = $(modalId).find('.notice');
                        $notice.show().text(notice);
                        // This is for activating leanModal links that were in the notice.
                        // We should have a cleaner way of allowing all dynamically added leanmodal links to work.
                        $notice.find('a[rel*=leanModal]').leanModal({
                            top: 120,
                            overlay: 1,
                            closeButton: '.close-modal',
                            position: 'absolute'
                        });
                    }
                    e.preventDefault();
                });
            });
        }
    });

    $(document).ready(function($) {  // eslint-disable-line no-shadow
        $('button[rel*=leanModal]').each(function() {
            var sep, embed;

            $(this).leanModal({top: 120, overlay: 1, closeButton: '.close-modal', position: 'absolute'});
            embed = $($(this).attr('href')).find('iframe');
            if (embed.length > 0 && embed.attr('src')) {
                sep = (embed.attr('src').indexOf('?') > 0) ? '&' : '?';
                embed.data('src', embed.attr('src') + sep + 'autoplay=1&rel=0');
                embed.attr('src', '');
            }
        });
    });
})(jQuery);
